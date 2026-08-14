#!/usr/bin/env python
"""Test pgvector store implementation."""

import numpy as np
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Collection, Document, User
from rag.store import get_or_create_store

# Ensure required parent rows exist for the foreign keys on chunks
with SessionLocal() as db:
    user = db.scalar(select(User).where(User.id == "test-user"))
    if user is None:
        db.add(
            User(
                id="test-user",
                name="Test User",
                email="test@example.com",
                password_hash="dummyhash",
                role="user",
                created_at="2026-08-14T00:00:00Z",
            )
        )

    collection = db.scalar(select(Collection).where(Collection.id == "test-collection"))
    if collection is None:
        db.add(
            Collection(
                id="test-collection",
                name="Test Collection",
                owner_id="test-user",
                visibility="private",
                created_at="2026-08-14T00:00:00Z",
            )
        )

    doc = db.scalar(select(Document).where(Document.id == "doc-1"))
    if doc is None:
        db.add(
            Document(
                id="doc-1",
                collection_id="test-collection",
                name="test.pdf",
                uri="/tmp/test.pdf",
                hash="hash123",
                pages=1,
                status="parsed",
                created_at="2026-08-14T00:00:00Z",
            )
        )

    db.commit()

# Create store
store = get_or_create_store("test-collection", 384)

# Add test vectors
vectors = np.random.randn(10, 384).astype(np.float32)
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

metas = [{"doc_id": "doc-1", "text": f"chunk {i}", "page": i} for i in range(10)]
store.add(vectors, metas)
print("✅ Added 10 vectors")

# Search
query = vectors[0]
results = store.search(query, k=5)
print(f"✅ Found {len(results)} results")
for meta, score in results:
    print(f"  - {meta['text']}: {score:.3f}")
