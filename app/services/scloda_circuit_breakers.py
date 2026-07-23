"""Circuit breakers for Scloda tools and upstream model providers."""

from __future__ import annotations

import json
import time
from typing import Any

from app.extensiones import redis_client
from app.ml.logging_utils import get_logger

logger = get_logger("scloda.circuit")

TOOL_FAILURE_THRESHOLD = 3
TOOL_COOLDOWN_SECONDS = 300
MODEL_FAILURE_THRESHOLD = 4
MODEL_COOLDOWN_SECONDS = 180

_memory_state: dict[str, dict[str, Any]] = {}


def _key(namespace: str, name: str) -> str:
    return f"scloda:circuit:{namespace}:{name}"


def _load_state(key: str) -> dict[str, Any]:
    if redis_client is not None:
        try:
            raw = redis_client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.warning("circuit_redis_read_failed", error=str(exc))
    return _memory_state.get(key, {"failures": 0, "opened_until": 0})


def _save_state(key: str, state: dict[str, Any]) -> None:
    if redis_client is not None:
        try:
            redis_client.set(key, json.dumps(state), ex=max(TOOL_COOLDOWN_SECONDS, MODEL_COOLDOWN_SECONDS) * 2)
            return
        except Exception as exc:
            logger.warning("circuit_redis_write_failed", error=str(exc))
    _memory_state[key] = state


def _is_open(namespace: str, name: str) -> bool:
    state = _load_state(_key(namespace, name))
    return float(state.get("opened_until", 0) or 0) > time.time()


def allow_tool(tool_name: str) -> tuple[bool, str | None]:
    if _is_open("tool", tool_name):
        return False, "tool_circuit_open"
    return True, None


def record_tool_success(tool_name: str) -> None:
    _save_state(_key("tool", tool_name), {"failures": 0, "opened_until": 0})


def record_tool_failure(tool_name: str) -> None:
    key = _key("tool", tool_name)
    state = _load_state(key)
    failures = int(state.get("failures", 0) or 0) + 1
    opened_until = 0
    if failures >= TOOL_FAILURE_THRESHOLD:
        opened_until = time.time() + TOOL_COOLDOWN_SECONDS
    _save_state(key, {"failures": failures, "opened_until": opened_until})


def allow_model(model_name: str) -> tuple[bool, str | None]:
    if _is_open("model", model_name):
        return False, "model_circuit_open"
    return True, None


def record_model_success(model_name: str) -> None:
    _save_state(_key("model", model_name), {"failures": 0, "opened_until": 0})


def record_model_failure(model_name: str) -> None:
    key = _key("model", model_name)
    state = _load_state(key)
    failures = int(state.get("failures", 0) or 0) + 1
    opened_until = 0
    if failures >= MODEL_FAILURE_THRESHOLD:
        opened_until = time.time() + MODEL_COOLDOWN_SECONDS
    _save_state(key, {"failures": failures, "opened_until": opened_until})


def get_circuit_breaker_status() -> dict[str, Any]:
    now = time.time()
    result = []
    keys = list(_memory_state.keys())
    if redis_client is not None:
        try:
            keys = [key for key in redis_client.scan_iter("scloda:circuit:*")]
        except Exception:
            pass
    for key in keys:
        raw_key = key.decode("utf-8") if isinstance(key, bytes) else str(key)
        state = _load_state(raw_key)
        result.append(
            {
                "key": raw_key,
                "failures": int(state.get("failures", 0) or 0),
                "is_open": float(state.get("opened_until", 0) or 0) > now,
                "opened_until": float(state.get("opened_until", 0) or 0),
            }
        )
    return {"circuits": result}
