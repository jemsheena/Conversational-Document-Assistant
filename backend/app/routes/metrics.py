from typing import Dict

from fastapi import APIRouter

router = APIRouter()

# Simple in-memory metrics (can be upgraded to Prometheus)
metrics_store: Dict[str, list] = {"latencies": [], "token_counts": [], "retrieval_scores": []}


@router.get("")
async def get_metrics():
    """Get aggregated metrics."""
    latencies = metrics_store["latencies"]
    tokens = metrics_store["token_counts"]
    scores = metrics_store["retrieval_scores"]

    return {
        "latency_ms": {
            "mean": sum(latencies) / len(latencies) if latencies else 0,
            "p95": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            "count": len(latencies),
        },
        "tokens": {
            "total_in": sum(t.get("in", 0) for t in tokens),
            "total_out": sum(t.get("out", 0) for t in tokens),
            "count": len(tokens),
        },
        "retrieval_scores": {
            "mean": sum(scores) / len(scores) if scores else 0,
            "max": max(scores) if scores else 0,
            "count": len(scores),
        },
    }
