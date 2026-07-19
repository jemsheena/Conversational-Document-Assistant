# Architecture

This document describes the system architecture of the Conversational Document Assistant as it is actually implemented — a monolithic FastAPI backend, a React SPA frontend, and a Retrieval-Augmented Generation (RAG) pipeline built around FAISS and a pluggable LLM provider layer.

> **Note on scope:** this project does not use event sourcing, CQRS, sagas, or a message broker (Kafka). It is a synchronous request/response web application with a streaming (SSE) chat endpoint. The diagrams below reflect the pipeline and data-flow patterns that *are* present: a request/response API, a multi-stage retrieval pipeline, and an ingestion pipeline.

## 1. Overall Architecture

```mermaid
flowchart TB
    subgraph Client["Frontend — React 18 + Vite"]
        UI[Chat UI]
        Auth[Auth Pages]
        Upload[PDF Upload]
        Coll[Collections / Docs Pages]
    end

    subgraph API["Backend — FastAPI"]
        Routes[REST + SSE Routes]
        AuthM[JWT Middleware]
        IngestSvc[Ingest Service]
        ChatSvc[Chat Service]
        SearchSvc[Search Service]
        MetricsSvc[Metrics Service]
    end

    subgraph RAG["RAG Engine (backend/rag)"]
        PDF[PDF Parser]
        Chunk[Chunker]
        Embed[Embedder]
        FAISS[(FAISS Index)]
        Rerank[Cross-Encoder Reranker]
        Prompt[Prompt Builder]
        LLM[LLM Provider Adapter]
        Cache[Query Cache]
    end

    subgraph Data["Persistence"]
        PG[(PostgreSQL)]
        Blob[(Local Disk / AWS S3)]
        IDX[(Vector Indices on Disk)]
    end

    UI --> Routes
    Auth --> AuthM
    Upload --> IngestSvc
    Coll --> Routes
    Routes --> ChatSvc
    Routes --> SearchSvc
    Routes --> MetricsSvc

    IngestSvc --> PDF --> Chunk --> Embed --> FAISS
    ChatSvc --> Cache
    Cache -.miss.-> FAISS
    FAISS --> Rerank --> Prompt --> LLM
    LLM -->|SSE stream| Routes

    IngestSvc --> PG
    IngestSvc --> Blob
    FAISS --> IDX
    AuthM --> PG
    MetricsSvc --> PG
```

**Key characteristics:**

- **Monolithic backend** — a single FastAPI service exposes all routes (`auth`, `collections`, `ingest`, `chat`, `search`, `docs`, `metrics`). There are no separate microservices.
- **Stateless API, stateful storage** — the API itself holds no session state beyond an in-process query cache; durable state lives in PostgreSQL (metadata) and on disk/S3 (PDF blobs, FAISS indices).
- **Streaming responses** — the `/api/chat` endpoint streams tokens to the client via Server-Sent Events rather than blocking for the full LLM response.

## 2. Module Dependencies

```mermaid
flowchart LR
    routes_auth[routes/auth.py] --> auth_utils[auth_utils.py]
    routes_auth --> database[database.py]

    routes_ingest[routes/ingest.py] --> rag_pdf[rag/pdf.py]
    routes_ingest --> rag_chunk[rag/chunk.py]
    routes_ingest --> rag_embed[rag/embed.py]
    routes_ingest --> rag_store[rag/store.py]
    routes_ingest --> storage[storage.py]
    routes_ingest --> database

    routes_chat[routes/chat.py] --> rag_store
    routes_chat --> rag_rerank[rag/rerank.py]
    routes_chat --> rag_prompt[rag/prompt.py]
    routes_chat --> rag_generate[rag/generate.py]
    routes_chat --> rag_cache[rag/cache.py]
    routes_chat --> rag_utils[rag/utils.py]
    routes_chat --> database

    routes_search[routes/search.py] --> rag_store
    routes_search --> rag_embed

    routes_collections[routes/collections.py] --> database
    routes_docs[routes/docs.py] --> database
    routes_metrics[routes/metrics.py] --> database

    rag_generate --> config[config.py]
    rag_embed --> config
    database --> config
    storage --> config

    main[app/main.py] --> routes_auth
    main --> routes_ingest
    main --> routes_chat
    main --> routes_search
    main --> routes_collections
    main --> routes_docs
    main --> routes_metrics
```

The `rag/` package has no dependency on `app/routes/` — it is pure pipeline logic invoked *by* the routes, which keeps the retrieval/generation code testable and provider-agnostic.

## 3. Document Ingestion Flow

```mermaid
sequenceDiagram
    participant U as User (Frontend)
    participant R as POST /api/ingest
    participant P as PDF Parser
    participant C as Chunker
    participant E as Embedder
    participant F as FAISS Store
    participant D as PostgreSQL
    participant S as Storage (Local/S3)

    U->>R: Upload PDF (multipart)
    R->>R: Validate type + size (<=50MB)
    R->>S: Persist PDF blob
    R->>D: Insert Document row (hash, status="parsed")
    R->>P: Extract per-page text (PyMuPDF)
    P->>C: Raw text per page
    C->>C: Split into ~900-token chunks, 120-token overlap
    C->>E: Chunk batch
    E->>E: Encode with MiniLM-L6-v2 (384-dim, normalized)
    E->>F: Add vectors to per-collection FAISS index
    F->>D: Persist chunk metadata (page, section, tokens)
    R-->>U: 200 OK — document indexed
```

## 4. Chat / Retrieval Flow (RAG Pipeline)

```mermaid
sequenceDiagram
    participant U as User (Frontend)
    participant R as POST /api/chat (SSE)
    participant Cache as Query Cache
    participant F as FAISS Store
    participant RR as Cross-Encoder Reranker
    participant PB as Prompt Builder
    participant LLM as LLM Provider (Groq/OpenAI/HF/Ollama)

    U->>R: query, collection, k, rerank_k, model
    R->>Cache: lookup(SHA-256 of query + params)
    alt cache hit
        Cache-->>R: cached reranked passages
    else cache miss
        R->>F: search(query embedding, K=12)
        F-->>R: top-K passages
        R->>RR: rerank(query, passages)
        RR-->>R: top rerank_k passages (diversified)
        R->>Cache: store(key, passages, TTL=600s)
    end
    R->>PB: build grounded prompt (numbered sources, 8K token budget)
    PB-->>R: system + user prompt
    R->>LLM: stream completion
    loop token stream
        LLM-->>R: token
        R-->>U: SSE {"token": "...", "done": false}
    end
    R->>R: validate [N] citations against source indices
    R-->>U: SSE {"done": true, "sources": [...], "citation_valid": bool}
    R->>PostgreSQL: log retrieval (latency, model, k, r)
```

## 5. Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as /api/auth/*
    participant D as PostgreSQL

    U->>R: POST /register (name, email, password)
    R->>R: bcrypt hash password
    R->>D: insert User
    R-->>U: 201 Created

    U->>R: POST /login (email, password)
    R->>D: fetch User by email
    R->>R: verify bcrypt hash
    R->>R: issue JWT access (15 min) + refresh (7 day)
    R-->>U: {access_token, refresh_token}

    U->>R: POST /refresh (refresh_token)
    R->>R: verify refresh token signature/expiry
    R-->>U: new access_token
```

## Deployment View

```mermaid
flowchart LR
    subgraph GH["GitHub"]
        Push[Push to main] --> CI[CI: lint + test]
        CI --> Build[Build Docker images]
        Build --> GHCR[(GHCR registry)]
    end

    GHCR --> Deploy[Deploy step — SSH to EC2]

    subgraph EC2["AWS EC2 (Docker Compose)"]
        FE[Frontend container — Nginx]
        BE[Backend container — Uvicorn]
        PGc[(PostgreSQL container)]
    end

    Deploy --> FE
    Deploy --> BE
    Deploy --> PGc
    BE --> S3[(AWS S3 — PDF storage, via IAM role)]
```

---

Not every request path is diagrammed above (e.g. collections CRUD, metrics aggregation) since they are straightforward CRUD/read operations against PostgreSQL with no additional pipeline logic worth visualizing.
