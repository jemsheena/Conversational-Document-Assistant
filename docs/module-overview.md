# Module Overview

A per-module reference for the backend and frontend codebases. See [architecture.md](architecture.md) for how these modules interact, and [design-decisions.md](design-decisions.md) for the reasoning behind key choices.

## Backend — `backend/app/`

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app instantiation, CORS setup, router registration, startup DB init, `/health` endpoint |
| `config.py` | Centralized `Settings` class — reads all configuration from environment variables with sensible defaults |
| `database.py` | SQLAlchemy engine/session setup, `init_database()` table creation |
| `models.py` | SQLAlchemy ORM models: `User`, `Collection`, `CollectionMember`, `Document`, `Chunk`, `Chat`, `Message`, `RetrievalLog` |
| `auth_utils.py` | Password hashing (bcrypt), JWT encode/decode helpers |
| `storage.py` | Storage abstraction over local disk and AWS S3 for PDF blobs |
| `deps.py` | FastAPI dependency-injection helpers (e.g. current-user resolution from JWT) |
| `dto/` | Pydantic request/response schemas, separated by domain (`chat.py`, `ingest.py`, `common.py`) |

### `backend/app/routes/`

| Route module | Endpoints | Responsibility |
|---|---|---|
| `auth.py` | `/api/auth/register`, `/login`, `/refresh` | Account creation, login, token refresh |
| `collections.py` | `/api/collections` (GET/POST) | Create/list document collections |
| `ingest.py` | `/api/ingest` (POST) | Accept PDF uploads, drive the ingestion pipeline |
| `chat.py` | `/api/chat` (POST, SSE) | Drive the retrieval + generation pipeline, stream tokens |
| `search.py` | `/api/search` (GET) | Direct semantic search over a collection (no generation) |
| `docs.py` | `/api/docs` (GET) | List indexed documents |
| `metrics.py` | `/api/metrics` (GET) | Aggregated latency/token/retrieval-score stats |

## Backend — `backend/rag/` (RAG Engine)

This package contains the retrieval and generation pipeline and has no dependency on the FastAPI layer — it's invoked by routes, not the other way around.

| Module | Responsibility |
|---|---|
| `pdf.py` | Per-page text extraction from PDFs (PyMuPDF) |
| `chunk.py` | Token-aware chunking (tiktoken `cl100k_base`), 900-token chunks / 120-token overlap |
| `embed.py` | Embedding generation via Sentence-Transformers (`all-MiniLM-L6-v2`) or OpenAI embeddings |
| `store.py` | FAISS vector store — per-collection index creation, add, and similarity search |
| `rerank.py` | Cross-encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`) of FAISS candidates |
| `prompt.py` | Grounded prompt construction — injects numbered sources, enforces an 8K-token context budget |
| `generate.py` | Multi-provider LLM streaming client (Groq / OpenAI / Hugging Face / local Ollama) |
| `cache.py` | SHA-256-keyed, TTL-based in-memory cache for reranked retrieval results |
| `utils.py` | Passage diversification (per-doc/page limits) and post-generation citation validation |

## Backend — supporting directories

| Directory | Purpose |
|---|---|
| `alembic/` | Database migration scripts (SQLAlchemy/Alembic) |
| `scripts/` | Operational scripts — `init_db.py` (schema init), `test_groq.py` (manual Groq connectivity smoke test) |
| `tests/` | Pytest suite — currently covers the health endpoint and local storage backend |

## Frontend — `frontend/src/`

| Directory | Responsibility |
|---|---|
| `pages/` | Route-level views: `Auth.jsx` (login/signup), `Chat.jsx` (main chat workspace), `Collections.jsx`, `Documents.jsx`, `Settings.jsx`, `Uploads.jsx` |
| `components/` | Reusable UI: `Layout.jsx` (shell/nav), `Message.jsx` (chat bubble + citations), `Modal.jsx`, `Onboarding.jsx`, `SourcesDrawer.jsx` (citation source panel), `UploadModal.jsx` |
| `store/` | React context-based state: `useAuth.jsx` (auth/session), `useChat.jsx` (conversation state, SSE handling), `useCollections.jsx` |
| `api/client.js` | Thin fetch wrapper for calling the backend REST/SSE API |

## Deployment & tooling (repo root)

| Path | Purpose |
|---|---|
| `docker-compose.yml` / `docker-compose.prod.yml` | Local dev stack / production EC2 stack definitions |
| `.github/workflows/ci-cd.yml` | Lint → test → build → push (GHCR) → deploy (EC2) pipeline |
| `deploy/` | AWS/EC2 deployment tooling — ECS task definitions, deploy scripts, Windows connection helpers |
| `.env.example` | Full reference of supported environment variables |
| `GROQ_INTEGRATION.md` | Deep-dive on the default LLM provider setup and switching providers |
