"""Optional export hooks for Langfuse and Phoenix."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from app.ml.logging_utils import get_logger

logger = get_logger("scloda.external_obs")

LANGFUSE_ENABLED = os.getenv("SCLODA_ENABLE_LANGFUSE", "false").lower() == "true"
PHOENIX_ENABLED = os.getenv("SCLODA_ENABLE_PHOENIX", "false").lower() == "true"

try:
    from langfuse import get_client as get_langfuse_client
    from langfuse import observe as langfuse_observe

    LANGFUSE_SDK_AVAILABLE = True
except Exception:
    LANGFUSE_SDK_AVAILABLE = False
    get_langfuse_client = None
    langfuse_observe = None

try:
    from phoenix.otel import register as register_phoenix
    from opentelemetry import trace

    PHOENIX_SDK_AVAILABLE = True
except Exception:
    PHOENIX_SDK_AVAILABLE = False
    register_phoenix = None
    trace = None


@lru_cache(maxsize=1)
def _langfuse_client():
    if not (LANGFUSE_ENABLED and LANGFUSE_SDK_AVAILABLE):
        return None
    try:
        client = get_langfuse_client()
        return client if client.auth_check() else None
    except Exception as exc:
        logger.warning("langfuse_init_failed", error=str(exc))
        return None


@lru_cache(maxsize=1)
def _phoenix_tracer():
    if not (PHOENIX_ENABLED and PHOENIX_SDK_AVAILABLE):
        return None
    try:
        provider = register_phoenix(
            project_name=os.getenv("PHOENIX_PROJECT_NAME", "scloda"),
            auto_instrument=False,
        )
        return trace.get_tracer("scloda") if provider else None
    except Exception as exc:
        logger.warning("phoenix_init_failed", error=str(exc))
        return None


def export_trace_payload(payload: dict[str, Any]) -> None:
    """Best-effort export of a persisted trace to optional external backends."""
    if LANGFUSE_ENABLED and LANGFUSE_SDK_AVAILABLE:
        client = _langfuse_client()
        if client and langfuse_observe:
            try:
                _export_langfuse(payload, client)
            except Exception as exc:
                logger.warning("langfuse_export_failed", error=str(exc))

    if PHOENIX_ENABLED and PHOENIX_SDK_AVAILABLE:
        tracer = _phoenix_tracer()
        if tracer:
            try:
                _export_phoenix(payload, tracer)
            except Exception as exc:
                logger.warning("phoenix_export_failed", error=str(exc))


def _export_langfuse(payload: dict[str, Any], client: Any) -> None:
    @langfuse_observe(name="scloda-trace-export")
    def _emit() -> None:
        client.update_current_trace(
            session_id=payload.get("trace_id"),
            user_id=str(payload.get("user_id")) if payload.get("user_id") else None,
            tags=[
                "scloda",
                f"status:{payload.get('response_status', 'unknown')}",
                f"task:{payload.get('task_type', 'unknown')}",
            ],
            input=payload.get("user_message"),
            output=payload.get("response_text"),
        )
        client.update_current_span(
            input={
                "tools_used": payload.get("tools_used", []),
                "confidence": payload.get("confidence"),
            },
            output={
                "error_code": payload.get("error_code"),
                "judge_summary": payload.get("judge_summary"),
            },
        )

    _emit()


def _export_phoenix(payload: dict[str, Any], tracer: Any) -> None:
    with tracer.start_as_current_span("scloda.chat.trace") as span:
        span.set_attribute("scloda.trace_id", payload.get("trace_id", ""))
        span.set_attribute("scloda.status", payload.get("response_status", ""))
        span.set_attribute("scloda.task_type", payload.get("task_type", ""))
        span.set_attribute("scloda.confidence", payload.get("confidence") or "")
        span.set_attribute("scloda.model_resolved", payload.get("model_resolved") or "")
        span.set_attribute("scloda.total_tokens", int(payload.get("total_tokens", 0) or 0))
        span.set_attribute("scloda.latency_ms", int(payload.get("latency_ms", 0) or 0))


def get_external_observability_status() -> dict[str, Any]:
    return {
        "langfuse_enabled": LANGFUSE_ENABLED,
        "langfuse_sdk_available": LANGFUSE_SDK_AVAILABLE,
        "langfuse_ready": bool(_langfuse_client()) if LANGFUSE_ENABLED else False,
        "phoenix_enabled": PHOENIX_ENABLED,
        "phoenix_sdk_available": PHOENIX_SDK_AVAILABLE,
        "phoenix_ready": bool(_phoenix_tracer()) if PHOENIX_ENABLED else False,
    }
