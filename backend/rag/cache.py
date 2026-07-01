"""
Pipeline Stage 9: Query caching for retrieval results.
"""

import time
from typing import Dict, List, Optional

# In-memory cache (can be replaced with Redis in production)
_cache: Dict[str, Dict] = {}


def get_cache_ttl() -> int:
    """Get cache TTL from settings (lazy import to avoid circular deps)."""
    from app.config import settings

    return settings.CACHE_TTL_SECONDS


def get_cached_retrieval(query_hash: str) -> Optional[List[Dict]]:
    """
    Get cached retrieval results for a query.

    Args:
        query_hash: SHA256 hash of query+collection

    Returns:
        Cached passages or None if cache miss/expired
    """
    if query_hash not in _cache:
        return None

    entry = _cache[query_hash]
    if time.time() - entry["timestamp"] > get_cache_ttl():
        del _cache[query_hash]
        return None

    return entry["passages"]


def set_cached_retrieval(query_hash: str, passages: List[Dict]):
    """
    Cache retrieval results for a query.

    Args:
        query_hash: SHA256 hash of query+collection
        passages: Retrieved and reranked passages
    """
    _cache[query_hash] = {"passages": passages, "timestamp": time.time()}

    # Simple LRU: if cache too large, remove oldest entries
    if len(_cache) > 1000:
        sorted_items = sorted(_cache.items(), key=lambda x: x[1]["timestamp"])
        for key, _ in sorted_items[:100]:  # Remove oldest 100
            del _cache[key]


def clear_cache():
    """Clear all cached entries."""
    _cache.clear()
