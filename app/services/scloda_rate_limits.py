"""Redis-backed request limits for Scloda endpoints."""

from __future__ import annotations

import os
import time
from typing import Any

from app.extensiones import redis_client

RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("SCLODA_RATE_LIMIT_WINDOW_SECONDS", "60"))
CHAT_RATE_LIMIT_MAX = int(os.getenv("SCLODA_CHAT_RATE_LIMIT_MAX", "12"))
INSIGHT_RATE_LIMIT_MAX = int(os.getenv("SCLODA_INSIGHT_RATE_LIMIT_MAX", "24"))
MODEL_ANALYSIS_RATE_LIMIT_MAX = int(
    os.getenv("SCLODA_MODEL_ANALYSIS_RATE_LIMIT_MAX", "12")
)


def _limit_key(scope: str, subject: str) -> str:
    current_window = int(time.time() // RATE_LIMIT_WINDOW_SECONDS)
    return f"scloda:rl:{scope}:{subject}:{current_window}"


def _check(scope: str, subject: str, max_requests: int) -> dict[str, Any]:
    if not subject:
        subject = "anonymous"

    if redis_client is None:
        return {
            "allowed": True,
            "remaining": max_requests,
            "limit": max_requests,
            "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
            "reset_in_seconds": RATE_LIMIT_WINDOW_SECONDS,
            "backend": "disabled",
        }

    key = _limit_key(scope, subject)
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, RATE_LIMIT_WINDOW_SECONDS)
    ttl = redis_client.ttl(key)
    remaining = max(0, max_requests - current)
    return {
        "allowed": current <= max_requests,
        "remaining": remaining,
        "limit": max_requests,
        "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
        "reset_in_seconds": max(0, ttl),
        "backend": "redis",
    }


def check_chat_limit(subject: str) -> dict[str, Any]:
    return _check("chat", subject, CHAT_RATE_LIMIT_MAX)


def check_insight_limit(subject: str) -> dict[str, Any]:
    return _check("insight", subject, INSIGHT_RATE_LIMIT_MAX)


def check_model_analysis_limit(subject: str) -> dict[str, Any]:
    return _check("model_analysis", subject, MODEL_ANALYSIS_RATE_LIMIT_MAX)
