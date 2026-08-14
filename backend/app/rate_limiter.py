"""
Rate limiting and usage tracking to prevent unexpected API bills.

Two layers:
1. Per-user per-minute rate limit (prevent spam/abuse)
2. Daily token budget (prevent runaway costs)
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from app.config import settings

# Per-user rate limiting: {user_id: [timestamp, timestamp, ...]}
request_log: Dict[str, list] = defaultdict(list)

# Daily token tracker: {user_id: {"tokens_used": N, "reset_at": timestamp}}
daily_tokens: Dict[str, dict] = defaultdict(
    lambda: {"tokens_used": 0, "reset_at": time.time() + 86400}
)


def check_rate_limit(user_id: str, limit_per_minute: int) -> Tuple[bool, str]:
    """
    Check if user has exceeded rate limit.

    Returns:
        (allowed, message)
    """
    now = time.time()
    user_requests = request_log[user_id]

    # Remove requests older than 1 minute
    user_requests[:] = [ts for ts in user_requests if now - ts < 60]

    if len(user_requests) >= limit_per_minute:
        return False, f"Rate limit exceeded: {limit_per_minute} requests per minute"

    user_requests.append(now)
    return True, "OK"


def track_token_usage(user_id: str, tokens_in: int, tokens_out: int) -> Tuple[bool, str, Dict]:
    """
    Track daily token usage per user.

    Returns:
        (allowed, message, usage_stats)
    """
    now = time.time()
    user_tracker = daily_tokens[user_id]

    # Reset if past the daily boundary
    if now > user_tracker.get("reset_at", 0):
        user_tracker["tokens_used"] = 0
        user_tracker["reset_at"] = now + 86400

    total_tokens = tokens_in + tokens_out
    new_total = user_tracker["tokens_used"] + total_tokens

    max_daily = settings.MAX_DAILY_TOKENS_PER_USER
    warning_threshold = settings.DAILY_TOKEN_WARNING_THRESHOLD_PERCENT

    usage_stats = {
        "tokens_used_today": new_total,
        "tokens_this_request": total_tokens,
        "daily_limit": max_daily,
        "percent_used": round((new_total / max_daily) * 100, 2),
    }

    user_tracker["tokens_used"] = new_total

    # Warn at threshold (default 80%)
    if new_total >= max_daily * (warning_threshold / 100):
        message = f"⚠️  Token budget alert: {usage_stats['percent_used']}% of daily limit used ({new_total:,} / {max_daily:,} tokens)"
        return True, message, usage_stats

    if new_total > max_daily:
        return False, f"Daily token budget exceeded: {new_total:,} / {max_daily:,}", usage_stats

    return True, "OK", usage_stats


def get_user_stats(user_id: str) -> Dict:
    """Get current usage stats for a user."""
    user_tracker = daily_tokens.get(user_id, {})
    now = time.time()

    # Check if need to reset
    if now > user_tracker.get("reset_at", 0):
        return {
            "tokens_used_today": 0,
            "daily_limit": settings.MAX_DAILY_TOKENS_PER_USER,
            "percent_used": 0.0,
        }

    tokens_used = user_tracker.get("tokens_used", 0)
    daily_limit = settings.MAX_DAILY_TOKENS_PER_USER
    return {
        "tokens_used_today": tokens_used,
        "daily_limit": daily_limit,
        "percent_used": round((tokens_used / daily_limit) * 100, 2),
    }
