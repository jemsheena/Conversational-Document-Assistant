"""Measure the actual local embedding + retrieval latency for this project.

Run from the backend directory:
    python scripts/measure_pipeline.py --queries "RAG helps ground answers" "document retrieval" --repeats 3
"""

import argparse
import json
import os
import statistics
import sys
import time
from typing import Iterable, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from rag.embed import get_embeddings  # noqa: E402
from rag.store import FaissStore  # noqa: E402


def _default_queries() -> List[str]:
    return [
        "How does retrieval augmented generation reduce hallucination?",
        "What is the difference between FAISS and pgvector?",
        "How are documents chunked and embedded for search?",
        "Why is reranking important in a document assistant?",
    ]


def _default_documents() -> List[str]:
    return [
        "Retrieval augmented generation grounds answers in retrieved passages instead of relying only on model memory.",
        "FAISS is a local in-memory vector index that is fast and simple for single-instance deployments.",
        "pgvector adds vector search to PostgreSQL, which is useful when multiple app instances share the same backend.",
        "Chunking splits large PDFs into smaller passages so each retrieval step is focused and relevant.",
        "Embedding models turn text into dense vectors that capture semantic similarity for nearest-neighbor search.",
        "Cross-encoder reranking improves ranking quality by comparing the query against candidate passages more carefully.",
        "A prompt builder injects the best retrieved snippets into the LLM context and keeps the answer grounded.",
        "Citation validation checks that every inline reference maps to a known source before the final answer is returned.",
    ]


def benchmark_pipeline(queries: Iterable[str], repeats: int = 3) -> dict:
    queries = list(queries)
    if not queries:
        raise ValueError("At least one query is required.")

    docs = _default_documents()
    embed_start = time.perf_counter()
    doc_vectors = get_embeddings(docs)
    doc_embed_ms = (time.perf_counter() - embed_start) * 1000

    store = FaissStore("pipeline_benchmark", doc_vectors.shape[1])
    store.add(doc_vectors, [{"text": d} for d in docs])

    embed_samples: List[float] = []
    search_samples: List[float] = []
    results: List[dict] = []

    for _ in range(repeats):
        for query in queries:
            t0 = time.perf_counter()
            query_vector = get_embeddings([query])[0]
            embed_ms = (time.perf_counter() - t0) * 1000
            embed_samples.append(embed_ms)

            t1 = time.perf_counter()
            matches = store.search(query_vector, k=5)
            search_ms = (time.perf_counter() - t1) * 1000
            search_samples.append(search_ms)
            results.append(
                {
                    "query": query,
                    "embed_ms": round(embed_ms, 2),
                    "search_ms": round(search_ms, 2),
                    "top_match": matches[0][0].get("text") if matches else None,
                    "top_score": round(matches[0][1], 4) if matches else None,
                }
            )

    def summarize(values: List[float]) -> dict:
        if not values:
            return {"avg_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0, "p95_ms": 0.0}
        ordered = sorted(values)
        return {
            "avg_ms": round(statistics.mean(values), 2),
            "min_ms": round(min(values), 2),
            "max_ms": round(max(values), 2),
            "p95_ms": round(ordered[max(0, int(len(ordered) * 0.95) - 1)], 2),
        }

    summary = {
        "documents": len(docs),
        "queries": len(queries),
        "repeats": repeats,
        "doc_index_build_ms": round(doc_embed_ms, 2),
        "embedding": summarize(embed_samples),
        "retrieval": summarize(search_samples),
        "samples": results,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure local embedding and retrieval latency.")
    parser.add_argument("--queries", nargs="*", default=None, help="Queries to test.")
    parser.add_argument("--repeats", type=int, default=3, help="Number of repeats per query.")
    args = parser.parse_args()

    queries = args.queries or _default_queries()
    summary = benchmark_pipeline(queries, repeats=args.repeats)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
