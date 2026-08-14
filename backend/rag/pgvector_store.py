"""
pgvector-based vector store for distributed deployments.

This module provides a PostgreSQL/pgvector alternative to FAISS for scenarios where
distributed vector search is needed (e.g., AlloyDB on GCP). The interface mirrors
FaissStore to enable easy switching.

Requirements:
  - PostgreSQL 13+ with pgvector extension
  - pip install pgvector
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Chunk

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

logger = logging.getLogger(__name__)


class PgvectorStore:
    """PostgreSQL/pgvector-based vector store for distributed deployments."""

    def __init__(self, collection_id: str, dim: int):
        """Initialize pgvector store for a collection.

        Args:
            collection_id: Collection identifier
            dim: Vector dimension (should be 384 for MiniLM-L6-v2)
        """
        if not PGVECTOR_AVAILABLE:
            raise ImportError(
                "pgvector package not installed. Install with: pip install pgvector"
            )

        self.collection_id = collection_id
        self.dim = dim
        self.db: Optional[Session] = None

        logger.info(
            f"🔌 Initialized PgvectorStore for collection '{collection_id}' (dim={dim})"
        )

    def _get_session(self) -> Session:
        """Get or create database session."""
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def add(self, vectors: np.ndarray, metas: List[Dict]):
        """Add vectors and metadata to the database.

        Args:
            vectors: numpy array of shape (n, dim), should be normalized
            metas: list of metadata dicts with keys: doc, page, text, etc.
        """
        if len(vectors) != len(metas):
            raise ValueError("Mismatch between vector count and metadata count")

        if vectors.shape[1] != self.dim:
            raise ValueError(
                f"Vector dimension mismatch: expected {self.dim}, got {vectors.shape[1]}"
            )

        # Normalize vectors (cosine similarity)
        vectors = vectors.astype(np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / (norms + 1e-8)

        db = self._get_session()

        try:
            for vector, meta in zip(vectors, metas):
                chunk = Chunk(
                    doc_id=meta.get("doc_id", ""),
                    collection_id=self.collection_id,
                    text=meta.get("text", ""),
                    page=meta.get("page"),
                    section=meta.get("section"),
                    bbox=meta.get("bbox"),
                    tokens=meta.get("tokens"),
                    embedding=vector.tolist(),  # pgvector stores as list
                )
                db.add(chunk)

            db.commit()
            logger.info(
                f"✅ Added {len(vectors)} vectors to PgvectorStore (collection={self.collection_id})"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error adding vectors to PgvectorStore: {e}")
            raise
        finally:
            db.close()
            self.db = None

    def search(self, query_vector: np.ndarray, k: int = 12) -> List[Tuple[Dict, float]]:
        """Search for similar vectors using cosine similarity.

        Args:
            query_vector: query embedding (1, dim)
            k: number of results to return

        Returns:
            List of (metadata, score) tuples, ordered by similarity (descending)
        """
        if query_vector.shape != (self.dim,):
            raise ValueError(
                f"Query vector shape mismatch: expected ({self.dim},), got {query_vector.shape}"
            )

        # Normalize query vector
        query_vector = query_vector.astype(np.float32)
        norm = np.linalg.norm(query_vector)
        query_vector = query_vector / (norm + 1e-8)
        query_vector_list = query_vector.tolist()

        db = self._get_session()

        try:
            # pgvector cosine_distance returns 0.0 for identical vectors and increases
            # as the vectors become less similar. For normalized vectors, convert to a
            # similarity score in [0, 1] via 1 - distance.
            cosine_distance = Chunk.embedding.cosine_distance(query_vector_list)
            results = db.execute(
                select(
                    Chunk.id,
                    Chunk.doc_id,
                    Chunk.text,
                    Chunk.page,
                    Chunk.section,
                    Chunk.embedding,
                    (1.0 - cosine_distance).label("similarity"),
                )
                .where(Chunk.collection_id == self.collection_id)
                .where(Chunk.embedding.isnot(None))
                .order_by(cosine_distance.asc())
                .limit(k)
            ).fetchall()

            response = []
            for row in results:
                meta = {
                    "id": row.id,
                    "doc": row.doc_id,  # compat with FAISS store
                    "text": row.text,
                    "page": row.page,
                    "section": row.section,
                }
                score = float(row.similarity) if row.similarity else 0.0
                response.append((meta, score))

            return response
        finally:
            db.close()
            self.db = None

    def save(self):
        """Persist store (no-op for pgvector; data already in database)."""
        logger.info("💾 PgvectorStore data already persisted in database")
        pass


def get_or_create_pgvector_store(collection_id: str, dim: int) -> PgvectorStore:
    """Get or create a pgvector store for a collection.

    This is the factory function for pgvector. Use get_or_create_store()
    from store.py for provider-agnostic access.
    """
    return PgvectorStore(collection_id, dim)
