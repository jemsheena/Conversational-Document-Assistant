"""Add pgvector support for AlloyDB deployments.

Revision ID: 003
Revises: 002
Create Date: 2026-08-14

This migration adds pgvector extension and embedding vector storage
to the chunks table, enabling distributed vector search on AlloyDB
as an alternative to local FAISS indices.
"""

import sqlalchemy as sa

from alembic import op

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column to chunks table
    # Uses vector(384) for sentence-transformers/all-MiniLM-L6-v2 dimension
    if Vector is not None:
        op.add_column(
            "chunks",
            sa.Column("embedding", Vector(384), nullable=True),
        )
    else:
        # Fallback: use raw SQL if pgvector not installed
        op.execute("ALTER TABLE chunks ADD COLUMN embedding vector(384)")

    # Create HNSW index for fast similarity search
    # HNSW is better for large datasets than IVFFlat
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
        ON chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m=16, ef_construction=64)
        """
    )

    # Create partial index on non-null embeddings for query performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_collection_embedding
        ON chunks (collection_id)
        WHERE embedding IS NOT NULL
        """
    )


def downgrade() -> None:
    # Drop indices first
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_chunks_collection_embedding")

    # Drop embedding column
    op.drop_column("chunks", "embedding")

    # Drop pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")
