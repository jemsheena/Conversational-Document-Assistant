# Roadmap

This roadmap reflects planned work based on gaps in the current implementation. It is aspirational, not a commitment with dates — this is an actively evolving personal/portfolio project. See the [README's Current Implementation Status](../README.md#current-implementation-status) for what's already shipped.

## Near-term

- **Expand automated test coverage** — the current suite covers only the health endpoint and the local storage backend. Priority additions:
  - Unit tests for `rag/chunk.py` (boundary conditions on chunk size/overlap)
  - Unit tests for `rag/utils.py` citation validation logic
  - Integration test for the full ingest → chat round trip against a test FAISS index
- **Persist chat history server-side** — conversations currently live client-side; move to `Chat`/`Message` tables that already exist in the schema but aren't fully wired into the chat flow for history retrieval.
- **CI: real Postgres integration test** — the pipeline already spins up a PostgreSQL service container for backend tests; extend beyond current smoke coverage to exercise the ingest/chat routes against it.

## Mid-term

- **Additional document formats** — DOCX and plain text, reusing the existing chunk/embed/index pipeline (only the parsing stage — currently PyMuPDF/PDF-specific — needs to become format-aware).
- **Collection sharing & roles** — the `CollectionMember` table already models a `permission` field; the API/UI don't yet expose collection sharing beyond the owner.
- **Rate limiting beyond chat** — currently only `/api/chat` is rate-limited; ingestion and search could benefit from similar protection.

## Longer-term / exploratory

- **Alternative vector store for multi-instance deployments** — FAISS indices are local-disk today, which is a blocker for running more than one backend replica. Evaluate `pgvector` (keeps everything in the existing PostgreSQL instance) vs. a dedicated vector DB (e.g. Qdrant) for a horizontally-scaled deployment.
- **Hybrid retrieval (dense + sparse)** — combine the existing FAISS dense search with BM25 keyword search to improve recall on queries with exact terms/acronyms that embeddings can under-weight.
- **Observability** — export the existing `/api/metrics` aggregates in a Prometheus-compatible format for Grafana dashboards, rather than only exposing a JSON summary endpoint.

## Explicitly out of scope (for now)

- Kubernetes/orchestration beyond Docker Compose — not justified at the current scale.
- Multi-region deployment — single-region EC2 is sufficient for the project's current purpose.
