# Performance & Model Stack

This document details the models, vendors, and performance characteristics used in the Conversational Document Assistant.

## Embedding Model — `all-MiniLM-L6-v2`

| Metric | Value |
|---|---|
| Dimensions | 384 |
| Parameters | ~22M |
| Max sequence length | 256 tokens |
| STS Benchmark (Spearman) | ~0.84 |
| Typical inference speed | ~3,000 sentences/sec on CPU |

**Source:** [Sentence-Transformers model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

This is a relatively lightweight, high-quality embedding model that runs efficiently on CPU and provides good semantic similarity matching for RAG retrieval.

---

## Reranker — `cross-encoder/ms-marco-MiniLM-L-6-v2`

| Metric | Value |
|---|---|
| Parameters | ~22M |
| MS MARCO MRR@10 | ~0.387 |
| MS MARCO NDCG@10 | ~0.431 |
| Typical latency | ~15–25 ms per pair on CPU |

**Source:** [Cross-Encoder MS MARCO model card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2)

The cross-encoder is applied to the top-K retrieved candidates to re-rank them by query–passage relevance. This typically improves final answer quality compared to embedding-only ranking.

---

## LLM Provider — Groq (Default)

### Available Models

| Model | Context | Avg Latency | Throughput | Best For |
|---|---|---|---|---|
| `llama-3.3-70b-versatile` | 128K | ~1.0s | 300–500 tok/s | **Production Q&A (recommended)** |
| `llama-3.1-70b-versatile` | 128K | ~1.2s | 250–400 tok/s | High-quality alternative |
| `mixtral-8x7b-32768` | 32K | ~0.5s | 500–800 tok/s | Lowest latency |
| `gemma2-9b-it` | 8K | ~0.3s | 600–900 tok/s | Lightweight queries |

These are vendor-reported estimates and vary based on load, inference settings, and API conditions.

---

## Provider Comparison

| Provider | Typical Response Time | Tokens/Second | Cost (per 1M tokens) |
|---|---|---|---|
| **Groq (Mixtral)** | ~0.5s | 500–800 | $0.05–0.27 |
| **Groq (Llama 3.3)** | ~1.0s | 300–500 | $0.05–0.27 |
| OpenAI GPT-4o-mini | ~2–3s | 80–120 | $0.15 in / $0.60 out |
| OpenAI GPT-4 | ~3–5s | 50–100 | $5.00 in / $15.00 out |
| Hugging Face (free) | ~10–30s | 10–30 | Free tier |

Choose a provider based on your requirements for latency, quality, and cost. Groq is the default because of its fast inference and low cost; OpenAI offers higher quality but higher latency and cost; Hugging Face is free but slower.

---

## End-to-End Latency (Vendor Estimates)

| Phase | Duration (CPU, single query) |
|---|---|
| Embedding query | ~5–15 ms |
| Vector search (K=12) | ~1–5 ms |
| Cross-encoder rerank (12 pairs) | ~150–300 ms |
| Prompt assembly | ~1–5 ms |
| LLM first token (Groq) | ~200–500 ms |
| Full response (600 tokens) | ~1–2s |
| **Total (retrieval → complete answer)** | **~1.5–3s** |

> **Note:** These are directional estimates for a typical local setup and vary with corpus size, hardware, LLM provider, and network latency. Cached queries skip retrieval/reranking (~600s TTL).

---

## Measured Local Results

For **actual measured performance** from this codebase, see the "Measured Local Benchmark" section in the [main README](../README.md#measured-local-benchmark). You can reproduce results by running:

```bash
cd backend
python scripts/measure_pipeline.py --repeats 3
```

This gives you real numbers on your hardware instead of vendor estimates.

