# Design Decisions

This document records the significant design decisions made in this project and the reasoning behind them, based on the current implementation.

## 1. FAISS over a managed vector database

**Decision:** Use FAISS (`IndexFlatIP`) with one index per collection, persisted to local disk, instead of a managed/networked vector database (e.g. pgvector, Pinecone, Qdrant).

**Reasoning:**
- Zero external dependency for a single-node deployment — no extra service to run, monitor, or pay for.
- `IndexFlatIP` gives exact (not approximate) cosine similarity search, which is appropriate at the corpus sizes this project targets (a document collection per user/team, not a web-scale index).
- Embeddings are normalized before indexing so inner product is equivalent to cosine similarity.

**Trade-off accepted:** FAISS indices are local to the container filesystem, so the current design does not support horizontal scaling across multiple backend instances without a shared volume or a move to a networked vector store. This is called out explicitly in the [roadmap](roadmap.md).

## 2. Two-stage retrieval: FAISS search + cross-encoder rerank

**Decision:** Retrieve a broader candidate set from FAISS (`K=12`) and rerank with a cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) down to a smaller set (`rerank_k=6`) before building the prompt.

**Reasoning:**
- Bi-encoder (embedding) search is fast but less precise at ranking fine-grained relevance between a specific query and a specific passage.
- A cross-encoder, which scores the query and passage jointly, is significantly more accurate at reranking but too slow to run over an entire corpus — so it's only applied to the FAISS shortlist.
- This two-stage pattern is a well-established retrieval architecture that balances latency and precision.

**Trade-off accepted:** Reranking adds ~150–300ms of CPU latency per query (see README's latency table). This is mitigated by the 10-minute query result cache.

## 3. Token-aware chunking with overlap

**Decision:** Split extracted PDF text into ~900-token chunks (via `tiktoken`'s `cl100k_base` encoding) with 120-token overlap, rather than fixed character counts or sentence-based splitting alone.

**Reasoning:**
- Token counts map directly to LLM context budgets, so chunk sizing is predictable regardless of language or formatting density.
- Overlap reduces the chance that an answer-relevant sentence gets split across a chunk boundary and loses context on both sides.

## 4. Citation enforcement instead of trusting the LLM

**Decision:** The system prompt requires inline `[N]` citations, and the response is validated post-generation by checking that every citation index maps to an actual retrieved source. Source metadata (document, page, score, snippet) is always returned alongside the answer.

**Reasoning:**
- LLMs will happily generate plausible-sounding citations that don't correspond to real sources. Post-hoc validation catches this rather than trusting the model's output implicitly.
- Returning structured source metadata (rather than only citation numbers) lets the frontend build a "Sources" drawer without a second round-trip.

**Trade-off accepted:** Citation validation is presence/format validation (does `[N]` correspond to a real source), not a semantic check that the citation is contextually accurate. True faithfulness verification would require a separate model call, which was judged not worth the added latency/cost for this project's scope.

## 5. Multi-provider LLM abstraction

**Decision:** Support Groq, OpenAI, Hugging Face, and local (Ollama/LM Studio) providers behind a single `LLM_PROVIDER` config switch, all using an OpenAI-compatible chat completion interface where possible.

**Reasoning:**
- Groq is the default because of its inference speed (300–800 tok/s vs. 50–120 tok/s for typical OpenAI models), which matters for a chat UX with streaming responses.
- Supporting a local provider (Ollama) allows the project to run with zero external API costs for development/demo purposes.
- An OpenAI-compatible interface across providers minimizes provider-specific code paths in `rag/generate.py`.

## 6. JWT with short-lived access tokens + refresh tokens

**Decision:** 15-minute access tokens, 7-day refresh tokens, bcrypt password hashing, no server-side session store.

**Reasoning:**
- Short-lived access tokens limit the blast radius if a token is leaked (e.g. via logs or XSS), without requiring the user to log in every 15 minutes thanks to the refresh flow.
- Stateless JWTs avoid needing a session store (e.g. Redis) for a project of this scale.

**Trade-off accepted:** There's no server-side token revocation list, so a compromised token remains valid until it expires. This is an accepted trade-off for a project of this scope, not a production-hardened auth system for a multi-tenant SaaS.

## 7. Query result caching (in-memory, TTL-based)

**Decision:** Cache reranked retrieval results for 600 seconds, keyed by a SHA-256 hash of the query text and retrieval parameters.

**Reasoning:**
- Repeated or near-repeated questions (common in a chat UI, e.g. clarifying follow-ups referencing the same context) skip the ~150–300ms rerank cost and the FAISS search entirely.
- A simple in-memory TTL cache avoids introducing an external cache service (e.g. Redis) for a feature that's a latency optimization, not a correctness requirement.

**Trade-off accepted:** Cache is per-process and lost on restart, and does not scale across multiple backend instances. Acceptable given the single-node deployment target.

## 8. Docker Compose for both dev and production

**Decision:** Use Docker Compose (`docker-compose.yml` for dev, `docker-compose.prod.yml` for the EC2 deployment) instead of Kubernetes or a managed container platform.

**Reasoning:**
- The application is a small number of services (frontend, backend, PostgreSQL) that fit comfortably on a single EC2 instance — Kubernetes' orchestration features (multi-node scheduling, auto-scaling) aren't needed at this scale.
- Docker Compose keeps the deployment story simple enough to document and reproduce in a README, which matters for an open-source/portfolio project.

## 9. Local disk storage in dev, S3 in production

**Decision:** PDF blobs are stored on local disk by default (`STORAGE_BACKEND=local`) and can be switched to AWS S3 (`STORAGE_BACKEND=s3`) via configuration, with an IAM role (not static credentials) used on EC2.

**Reasoning:**
- Local disk storage requires zero AWS setup for local development or evaluation.
- S3 with an IAM role avoids storing AWS access keys in `.env` on the production host, reducing the blast radius of a leaked `.env` file.
