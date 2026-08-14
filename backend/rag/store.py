import json
import os
from typing import Dict, List, Tuple, Union

import faiss
import numpy as np

from app.config import settings

_stores: Dict[str, Union["FaissStore", "PgvectorStore"]] = {}


class FaissStore:
    """FAISS vector store with metadata persistence."""

    def __init__(self, collection_id: str, dim: int):
        self.collection_id = collection_id
        self.dim = dim
        self.index_dir = os.path.join(settings.INDEX_DIR, collection_id)
        os.makedirs(self.index_dir, exist_ok=True)

        # Initialize index (Inner Product for cosine similarity on normalized vectors)
        self.index = faiss.IndexFlatIP(dim)
        self.meta: List[Dict] = []

        # Try to load existing
        self._load()

    def _load(self):
        """Load existing index and metadata if available."""
        index_path = os.path.join(self.index_dir, "index.faiss")
        meta_path = os.path.join(self.index_dir, "meta.json")

        if os.path.exists(index_path) and os.path.exists(meta_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load existing index: {e}")

    def add(self, vectors: np.ndarray, metas: List[Dict]):
        """Add vectors and their metadata."""
        if len(vectors) != len(metas):
            raise ValueError("Mismatch between vector count and metadata count")

        vectors = vectors.astype(np.float32)

        # Normalize for cosine similarity (Inner Product on normalized = cosine)
        faiss.normalize_L2(vectors)

        self.index.add(vectors)
        self.meta.extend(metas)

    def search(self, query_vector: np.ndarray, k: int = 12) -> List[Tuple[Dict, float]]:
        """Search for top-k similar vectors."""
        if self.index.ntotal == 0:
            return []

        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_vector)

        distances, indices = self.index.search(query_vector, min(k, self.index.ntotal))

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.meta):
                results.append((self.meta[idx], float(dist)))

        return results

    def save(self):
        """Persist index and metadata to disk."""
        index_path = os.path.join(self.index_dir, "index.faiss")
        meta_path = os.path.join(self.index_dir, "meta.json")

        faiss.write_index(self.index, index_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)


def get_or_create_store(collection_id: str, dim: int) -> Union[FaissStore, "PgvectorStore"]:
    """Get or create a vector store for a collection.

    Uses the configured VECTOR_STORE setting (faiss or pgvector).
    """
    if collection_id not in _stores:
        if settings.VECTOR_STORE.lower() == "pgvector":
            # Lazy import to avoid hard dependency on pgvector
            from rag.pgvector_store import PgvectorStore
            _stores[collection_id] = PgvectorStore(collection_id, dim)
        else:
            # Default to FAISS (local, single-instance)
            _stores[collection_id] = FaissStore(collection_id, dim)
    return _stores[collection_id]
