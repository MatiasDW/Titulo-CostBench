"""Human review queue and capability map for Scloda."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.extensiones import db
from app.ml.logging_utils import get_logger
from app.models.scloda import SclodaCapabilityNode, SclodaReviewQueueItem
from app.models.user import User

logger = get_logger("scloda.review")


def _ensure_review_tables() -> None:
    """Create only the review/capability tables owned by this service."""
    SclodaReviewQueueItem.__table__.create(bind=db.engine, checkfirst=True)
    SclodaCapabilityNode.__table__.create(bind=db.engine, checkfirst=True)

CAPABILITY_SEED = [
    {
        "slug": "scloda-core",
        "parent_slug": None,
        "label": "Scloda Core Brain",
        "domain": "core",
        "status": "active",
        "maturity_score": 68,
        "description": "Core orchestration, guardrails, routing, and grounded responses.",
        "metadata_json": {"kind": "root"},
    },
    {
        "slug": "scloda-real-estate",
        "parent_slug": "scloda-core",
        "label": "Real Estate Intelligence",
        "domain": "real_estate",
        "status": "active",
        "maturity_score": 58,
        "description": "Property metrics, affordability, dashboard interpretation, and market context.",
        "metadata_json": {"source": "current_product"},
    },
    {
        "slug": "scloda-trade",
        "parent_slug": "scloda-core",
        "label": "Trade Context",
        "domain": "markets",
        "status": "active",
        "maturity_score": 61,
        "description": "Macro, commodities, crypto, and paper-trading coaching.",
        "metadata_json": {"source": "current_product"},
    },
    {
        "slug": "scloda-news",
        "parent_slug": "scloda-core",
        "label": "News Interpretation",
        "domain": "news",
        "status": "active",
        "maturity_score": 49,
        "description": "News summarization and impact explanation with fallback data paths.",
        "metadata_json": {"source": "current_product"},
    },
    {
        "slug": "scloda-quantum-lab",
        "parent_slug": "scloda-core",
        "label": "Quantum Lab",
        "domain": "research",
        "status": "in_progress",
        "maturity_score": 24,
        "description": "Research space for quantum computing, neural-network experiments, and future agent capabilities.",
        "metadata_json": {"source": "planned_product"},
    },
    {
        "slug": "scloda-neural-memory",
        "parent_slug": "scloda-quantum-lab",
        "label": "Neural Memory",
        "domain": "research",
        "status": "in_progress",
        "maturity_score": 37,
        "description": "DB-backed retrieval memory, trace dataset growth, and controlled long-term knowledge.",
        "metadata_json": {"source": "current_iteration"},
    },
    {
        "slug": "scloda-neural-network",
        "parent_slug": "scloda-quantum-lab",
        "label": "Neural Network Training",
        "domain": "research",
        "status": "planned",
        "maturity_score": 18,
        "description": "Future space for labeled conversation sets, supervised tuning signals, and domain-specific learning loops.",
        "metadata_json": {"source": "roadmap"},
    },
    {
        "slug": "scloda-agent-topology",
        "parent_slug": "scloda-quantum-lab",
        "label": "Agent Topology Diagram",
        "domain": "research",
        "status": "in_progress",
        "maturity_score": 29,
        "description": "Visual map of guardrails, routing, memory, tools, and human review so future capabilities stay explainable.",
        "metadata_json": {"source": "roadmap"},
    },
    {
        "slug": "scloda-human-review",
        "parent_slug": "scloda-core",
        "label": "Human Review Queue",
        "domain": "safety",
        "status": "active",
        "maturity_score": 52,
        "description": "Escalation path for low-confidence or risky answers before product trust is damaged.",
        "metadata_json": {"source": "current_iteration"},
    },
    {
        "slug": "scloda-rag-docs",
        "parent_slug": "scloda-real-estate",
        "label": "Chile Real Estate Data Graph",
        "domain": "real_estate",
        "status": "in_progress",
        "maturity_score": 43,
        "description": "Roadmap toward combining SII, MINVU, INE, BDE, CBR, and live marketplace signals.",
        "metadata_json": {"source": "deep_research_report"},
    },
]


def ensure_capability_map_seeded() -> int:
    _ensure_review_tables()
    now = datetime.utcnow()
    existing_rows = {
        row.slug: row
        for row in SclodaCapabilityNode.query.all()
    }

    created = 0
    for item in CAPABILITY_SEED:
        row = existing_rows.get(item["slug"])
        if row is None:
            row = SclodaCapabilityNode(slug=item["slug"])
            db.session.add(row)
            created += 1

        row.parent_slug = item["parent_slug"]
        row.label = item["label"]
        row.domain = item["domain"]
        row.status = item["status"]
        row.maturity_score = item["maturity_score"]
        row.description = item["description"]
        row.metadata_json = item["metadata_json"]
        row.updated_at = now

    db.session.commit()
    return len(existing_rows) + created


def create_review_item(
    *,
    trace_id: str,
    user_id: int | None,
    task_type: str | None,
    reason: str,
    priority: str,
    model_resolved: str | None,
    user_message: str,
    agent_response: str,
) -> dict[str, Any]:
    _ensure_review_tables()
    existing = SclodaReviewQueueItem.query.filter_by(trace_id=trace_id).first()
    if existing:
        return existing.to_dict()

    row = SclodaReviewQueueItem(
        trace_id=trace_id,
        user_id=user_id,
        status="pending",
        priority=priority,
        reason=reason,
        task_type=task_type,
        model_resolved=model_resolved,
        notification_status="queued",
        notification_channel="in_app",
        user_message=user_message,
        agent_response=agent_response,
    )
    db.session.add(row)
    db.session.commit()
    return row.to_dict()


def list_review_items(
    status: str | None = None,
    limit: int = 50,
    assignee_user_id: int | None = None,
) -> list[dict[str, Any]]:
    _ensure_review_tables()
    query = SclodaReviewQueueItem.query.order_by(SclodaReviewQueueItem.created_at.desc())
    if status:
        query = query.filter(SclodaReviewQueueItem.status == status)
    if assignee_user_id is not None:
        query = query.filter(SclodaReviewQueueItem.assignee_user_id == assignee_user_id)
    return [row.to_dict() for row in query.limit(min(max(limit, 1), 200)).all()]


def assign_review_item(
    item_id: int,
    *,
    assignee_user_id: int | None,
    assignment_note: str | None = None,
) -> dict[str, Any] | None:
    _ensure_review_tables()
    row = db.session.get(SclodaReviewQueueItem, item_id)
    if row is None:
        return None

    assignee = None
    if assignee_user_id is not None:
        assignee = db.session.get(User, assignee_user_id)
        if assignee is None:
            return None

    row.assignee_user_id = assignee.id if assignee else None
    row.assignment_note = assignment_note or None
    row.assigned_at = datetime.utcnow() if assignee else None
    row.notification_status = "sent" if assignee else "queued"
    row.notification_sent_at = datetime.utcnow() if assignee else None
    db.session.commit()
    return row.to_dict()


def claim_review_item(item_id: int, reviewer_user_id: int) -> dict[str, Any] | None:
    return assign_review_item(
        item_id,
        assignee_user_id=reviewer_user_id,
        assignment_note="Claimed from admin queue.",
    )


def resolve_review_item(
    item_id: int,
    *,
    reviewer_notes: str,
    resolution_summary: str,
    status: str = "resolved",
) -> dict[str, Any] | None:
    _ensure_review_tables()
    row = db.session.get(SclodaReviewQueueItem, item_id)
    if row is None:
        return None
    row.status = status
    row.reviewer_notes = reviewer_notes
    row.resolution_summary = resolution_summary
    row.resolved_at = datetime.utcnow()
    db.session.commit()
    return row.to_dict()


def get_review_summary() -> dict[str, Any]:
    _ensure_review_tables()
    pending = SclodaReviewQueueItem.query.filter_by(status="pending").count()
    resolved = SclodaReviewQueueItem.query.filter_by(status="resolved").count()
    dismissed = SclodaReviewQueueItem.query.filter_by(status="dismissed").count()
    assigned_pending = SclodaReviewQueueItem.query.filter(
        SclodaReviewQueueItem.status == "pending",
        SclodaReviewQueueItem.assignee_user_id.isnot(None),
    ).count()
    unassigned_pending = SclodaReviewQueueItem.query.filter(
        SclodaReviewQueueItem.status == "pending",
        SclodaReviewQueueItem.assignee_user_id.is_(None),
    ).count()
    return {
        "pending": pending,
        "assigned_pending": assigned_pending,
        "unassigned_pending": unassigned_pending,
        "resolved": resolved,
        "dismissed": dismissed,
    }


def get_capability_tree() -> list[dict[str, Any]]:
    _ensure_review_tables()
    ensure_capability_map_seeded()
    rows = SclodaCapabilityNode.query.order_by(
        SclodaCapabilityNode.parent_slug.asc().nullsfirst(),
        SclodaCapabilityNode.domain.asc(),
        SclodaCapabilityNode.label.asc(),
    ).all()
    return [row.to_dict() for row in rows]
