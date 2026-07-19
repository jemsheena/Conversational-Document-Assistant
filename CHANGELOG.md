# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `docs/` directory with architecture, design-decision, module-overview, and roadmap documentation, including Mermaid diagrams for the overall architecture, module dependencies, ingestion flow, chat/retrieval flow, auth flow, and deployment view.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, GitHub issue templates, and a pull request template.
- "Current Implementation Status", "Roadmap", "Future Improvements", and "Motivation" sections in the README.

### Changed
- Reorganized deployment tooling (`ecs-*.json`, `deploy-aws.*`, EC2 helper scripts, `scripts/`) into a single top-level `deploy/` directory for clarity.
- Moved `backend/init_db.py` and `backend/test_groq.py` into `backend/scripts/`.
- Updated CI workflow and helper scripts to reference the new `deploy/scripts/` path.

### Removed
- Committed build artifacts (`deploy_latest.tar.gz`, `frontend_deploy_latest.tar.gz`) — these are build outputs and should not be version-controlled; `.gitignore` updated accordingly.

## [1.0.0] — Initial release

### Added
- Full-stack RAG platform for chatting with PDF documents: FastAPI backend, React 18 + Vite frontend.
- PDF ingestion pipeline: PyMuPDF text extraction, token-aware chunking, Sentence-Transformers embeddings, per-collection FAISS indices.
- Two-stage retrieval: FAISS similarity search followed by cross-encoder reranking, with passage diversification.
- Grounded chat generation with inline `[N]` citations, post-generation citation validation, and streaming responses via Server-Sent Events.
- Multi-provider LLM support: Groq (default), OpenAI, Hugging Face, and local (Ollama/LM Studio).
- JWT-based authentication (access + refresh tokens), bcrypt password hashing.
- Document collections with per-user ownership.
- Query result caching (TTL-based) and a `/api/metrics` endpoint for latency/token/retrieval-score aggregates.
- Docker Compose stacks for local development and production (EC2).
- CI/CD pipeline: lint (Ruff, ESLint) → test (Pytest) → build Docker images → push to GHCR → deploy to EC2.
