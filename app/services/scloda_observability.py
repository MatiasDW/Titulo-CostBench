"""Persistence and admin summaries for Scloda traces."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from app.extensiones import db
from app.ml.logging_utils import get_logger
from app.services.scloda_external_observability import export_trace_payload
from app.models.scloda import SclodaTrace

logger = get_logger("scloda.observability")


def _ensure_trace_table() -> None:
    """Create only the Scloda trace table when bootstrapping a fresh DB."""
    SclodaTrace.__table__.create(bind=db.engine, checkfirst=True)


def persist_scloda_trace(payload: dict[str, Any]) -> None:
    """Best-effort trace persistence that never breaks the user path."""
    try:
        _ensure_trace_table()
        trace = SclodaTrace(
            trace_id=payload["trace_id"],
            user_id=payload.get("user_id"),
            request_kind=payload.get("request_kind", "chat"),
            task_type=payload.get("task_type"),
            user_message=payload.get("user_message", ""),
            response_text=payload.get("response_text"),
            history_count=payload.get("history_count", 0),
            screening_reason=payload.get("screening_reason"),
            guardrail_action=payload.get("guardrail_action"),
            response_status=payload.get("response_status", "ok"),
            confidence=payload.get("confidence"),
            error_code=payload.get("error_code"),
            model_requested=payload.get("model_requested"),
            model_resolved=payload.get("model_resolved"),
            embedding_model=payload.get("embedding_model"),
            judge_model=payload.get("judge_model"),
            tools_used=payload.get("tools_used", []),
            tool_payloads=payload.get("tool_payloads", []),
            retrieved_chunks=payload.get("retrieved_chunks", []),
            judge_summary=payload.get("judge_summary"),
            prompt_tokens=payload.get("prompt_tokens", 0),
            completion_tokens=payload.get("completion_tokens", 0),
            total_tokens=payload.get("total_tokens", 0),
            latency_ms=payload.get("latency_ms", 0),
        )
        db.session.add(trace)
        db.session.commit()
        export_trace_payload(payload)
    except Exception as exc:
        db.session.rollback()
        logger.warning("trace_persist_failed", error=str(exc))


def list_recent_traces(limit: int = 25, status: str | None = None) -> list[dict[str, Any]]:
    """Return recent traces for admin inspection."""
    _ensure_trace_table()
    query = SclodaTrace.query.order_by(SclodaTrace.created_at.desc())
    if status:
        query = query.filter(SclodaTrace.response_status == status)
    rows = query.limit(min(max(limit, 1), 100)).all()
    return [row.to_dict() for row in rows]


def get_trace_summary(days: int = 7) -> dict[str, Any]:
    """Aggregate recent trace health metrics for a simple observability panel."""
    _ensure_trace_table()
    cutoff = datetime.utcnow() - timedelta(days=max(days, 1))
    rows = (
        SclodaTrace.query.filter(SclodaTrace.created_at >= cutoff)
        .order_by(SclodaTrace.created_at.desc())
        .all()
    )

    if not rows:
        return {
            "window_days": days,
            "total_traces": 0,
            "status_breakdown": {},
            "guardrail_actions": {},
            "models": {},
            "judge_verdicts": {},
            "avg_latency_ms": 0,
            "avg_tokens": 0,
            "knowledge_hit_rate": 0,
        }

    status_counter = Counter(row.response_status for row in rows if row.response_status)
    guardrail_counter = Counter(
        row.guardrail_action for row in rows if row.guardrail_action
    )
    model_counter = Counter(row.model_resolved for row in rows if row.model_resolved)
    judge_counter = Counter(
        (row.judge_summary or {}).get("final_verdict")
        for row in rows
        if row.judge_summary and (row.judge_summary or {}).get("final_verdict")
    )
    error_counter = Counter(row.error_code for row in rows if row.error_code)
    tool_counter = Counter()
    for row in rows:
        for tool_name in row.tools_used or []:
            tool_counter[tool_name] += 1

    knowledge_hits = sum(1 for row in rows if row.retrieved_chunks)
    total_tokens = sum(row.total_tokens for row in rows)
    total_latency = sum(row.latency_ms for row in rows)

    return {
        "window_days": days,
        "total_traces": len(rows),
        "status_breakdown": dict(status_counter),
        "guardrail_actions": dict(guardrail_counter),
        "models": dict(model_counter),
        "judge_verdicts": dict(judge_counter),
        "top_errors": dict(error_counter.most_common(5)),
        "top_tools": dict(tool_counter.most_common(10)),
        "avg_latency_ms": round(total_latency / len(rows), 2),
        "avg_tokens": round(total_tokens / len(rows), 2),
        "knowledge_hit_rate": round(knowledge_hits / len(rows), 4),
    }
