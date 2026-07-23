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
        "metadata_json": {
            "kind": "root",
            "focus": "Production orchestration",
            "interactive_note": "Click any child branch to inspect live signals, gaps, and next training work.",
            "progress_breakdown": [
                {
                    "label": "Routing + tool use",
                    "value": 82,
                    "detail": "Single-agent routing, task classification, and production tool calling are already live."
                },
                {
                    "label": "Grounding quality",
                    "value": 71,
                    "detail": "pgvector-backed retrieval and DB knowledge cache exist, but coverage is still uneven by domain."
                },
                {
                    "label": "Learning loop",
                    "value": 44,
                    "detail": "Trace capture and review queue exist, but there is no true supervised model-training pipeline yet."
                },
                {
                    "label": "Observability",
                    "value": 63,
                    "detail": "Internal traces and summaries exist, but external observability and richer dashboards are still partial."
                },
            ],
            "mermaid": "\nflowchart LR\n    U[User prompt] --> G[Guardrails]\n    G --> R[Task router]\n    R --> M[OpenRouter model]\n    M --> T[Tools + pgvector retrieval]\n    T --> C[Grounded answer]\n    C --> S[Confidence scoring]\n    S --> H{Low confidence?}\n    H -- no --> O[Output to user]\n    H -- yes --> Q[Human review queue]\n",
        },
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
        "metadata_json": {
            "source": "planned_product",
            "focus": "Research and training sandbox",
            "progress_breakdown": [
                {
                    "label": "Research framing",
                    "value": 62,
                    "detail": "The product direction is clear: neural training, domain graphs, and quantum research all have named tracks."
                },
                {
                    "label": "Interactive tooling",
                    "value": 28,
                    "detail": "The lab is becoming navigable, but there are not yet full admin actions that mutate or train models."
                },
                {
                    "label": "Trainable assets",
                    "value": 18,
                    "detail": "Useful data is being captured, but we do not yet have a formal labeled dataset or training runner."
                },
            ],
            "next_actions": [
                "Label real user conversations by task type and failure mode.",
                "Curate research modules for quantum + neural experiments.",
                "Build admin workflows that turn review outcomes into trainable data."
            ],
        },
    },
    {
        "slug": "scloda-neural-memory",
        "parent_slug": "scloda-quantum-lab",
        "label": "Neural Memory",
        "domain": "research",
        "status": "in_progress",
        "maturity_score": 37,
        "description": "DB-backed retrieval memory, trace dataset growth, and controlled long-term knowledge.",
        "metadata_json": {
            "source": "current_iteration",
            "focus": "Vector memory and reusable knowledge",
            "progress_breakdown": [
                {
                    "label": "Embedding storage",
                    "value": 78,
                    "detail": "Embeddings and native pgvector columns are already persisted in Postgres."
                },
                {
                    "label": "Coverage breadth",
                    "value": 34,
                    "detail": "Important documents and schema are indexed, but not every product dataset is yet embedded semantically."
                },
                {
                    "label": "Memory reuse",
                    "value": 29,
                    "detail": "The memory helps grounding today, but it is not yet feeding a closed-loop training system."
                },
            ],
            "next_actions": [
                "Expand semantic indexing beyond docs into more domain tables.",
                "Attach retrieval quality labels to successful and failed answers."
            ],
        },
    },
    {
        "slug": "scloda-neural-network",
        "parent_slug": "scloda-quantum-lab",
        "label": "Neural Network Training",
        "domain": "research",
        "status": "planned",
        "maturity_score": 18,
        "description": "Future space for labeled conversation sets, supervised tuning signals, and domain-specific learning loops.",
        "metadata_json": {
            "source": "roadmap",
            "focus": "Future supervised training",
            "progress_breakdown": [
                {
                    "label": "Dataset capture",
                    "value": 42,
                    "detail": "Traces, review queue outcomes, and retrieved context already create the raw substrate."
                },
                {
                    "label": "Human labeling",
                    "value": 19,
                    "detail": "The queue exists, but labeling conventions and adjudication flows are still minimal."
                },
                {
                    "label": "Training automation",
                    "value": 6,
                    "detail": "There is no current fine-tuning or recurrent training job running on the collected data."
                },
                {
                    "label": "Eval feedback loop",
                    "value": 14,
                    "detail": "There is some internal review logic, but not a formal closed loop from errors back into model updates."
                },
            ],
            "next_actions": [
                "Define labels for task type, failure mode, grounding quality, and reviewer verdict.",
                "Export approved conversations into train/validation slices.",
                "Train a small domain classifier or re-ranker before any larger model fine-tuning."
            ],
            "loop_steps": [
                {
                    "title": "Capture",
                    "subtitle": "Store prompts, answers, tools, chunks, latency, and confidence.",
                    "state": "live"
                },
                {
                    "title": "Review",
                    "subtitle": "Escalate weak answers into the admin queue for human feedback.",
                    "state": "live"
                },
                {
                    "title": "Label",
                    "subtitle": "Tag outcome, intent, domain, and failure cluster.",
                    "state": "next"
                },
                {
                    "title": "Assemble Dataset",
                    "subtitle": "Build supervised slices for tuning, ranking, or routing.",
                    "state": "planned"
                },
                {
                    "title": "Train + Evaluate",
                    "subtitle": "Run experiments and compare against live guardrails before release.",
                    "state": "planned"
                },
            ],
            "mermaid": "\nflowchart LR\n    A[User conversations + tool traces] --> B[Trace store]\n    B --> C[Human review queue]\n    C --> D[Intent + failure labels]\n    D --> E[Training dataset]\n    E --> F[Train classifier / reranker / future fine-tune]\n    F --> G[Offline evaluation]\n    G --> H[Safer routing + better answers]\n    H --> A\n",
        },
    },
    {
        "slug": "scloda-agent-topology",
        "parent_slug": "scloda-quantum-lab",
        "label": "Agent Topology Diagram",
        "domain": "research",
        "status": "in_progress",
        "maturity_score": 29,
        "description": "Visual map of guardrails, routing, memory, tools, and human review so future capabilities stay explainable.",
        "metadata_json": {
            "source": "roadmap",
            "focus": "Explainable system topology",
            "progress_breakdown": [
                {
                    "label": "System mapping",
                    "value": 61,
                    "detail": "The current flow from prompt to review is already documented and visible in-product."
                },
                {
                    "label": "Interactivity",
                    "value": 26,
                    "detail": "Nodes can now become navigable, but there are still no direct operator actions behind every branch."
                },
                {
                    "label": "Training visibility",
                    "value": 18,
                    "detail": "The learning loop is still mostly conceptual, not yet a live training control surface."
                },
            ],
            "mermaid": "\nflowchart TD\n    I[Inputs] --> C[Core agent]\n    C --> G[Grounding layer]\n    G --> T[Trust + confidence]\n    T --> R[Review queue]\n    R --> N[Neural training loop]\n    N --> C\n",
        },
    },
    {
        "slug": "scloda-human-review",
        "parent_slug": "scloda-core",
        "label": "Human Review Queue",
        "domain": "safety",
        "status": "active",
        "maturity_score": 52,
        "description": "Escalation path for low-confidence or risky answers before product trust is damaged.",
        "metadata_json": {
            "source": "current_iteration",
            "focus": "Human oversight",
            "progress_breakdown": [
                {
                    "label": "Escalation trigger",
                    "value": 71,
                    "detail": "Low-confidence and risky traces can already be persisted into a queue."
                },
                {
                    "label": "Reviewer tooling",
                    "value": 43,
                    "detail": "Claiming and resolving exist, but operator workflows are still shallow."
                },
                {
                    "label": "Training feedback",
                    "value": 31,
                    "detail": "Review outcomes are useful, but they are not yet systematically recycled into labeled training assets."
                },
            ],
        },
    },
    {
        "slug": "scloda-rag-docs",
        "parent_slug": "scloda-real-estate",
        "label": "Chile Real Estate Data Graph",
        "domain": "real_estate",
        "status": "in_progress",
        "maturity_score": 43,
        "description": "Roadmap toward combining SII, MINVU, INE, BDE, CBR, and live marketplace signals.",
        "metadata_json": {
            "source": "deep_research_report",
            "focus": "Real-estate data graph",
            "progress_breakdown": [
                {
                    "label": "Source definition",
                    "value": 74,
                    "detail": "Core Chilean real-estate sources are already identified and aligned to product use cases."
                },
                {
                    "label": "Integrated pipelines",
                    "value": 33,
                    "detail": "Some metrics and seeds exist, but the unified graph is not yet assembled."
                },
                {
                    "label": "Agent exploitation",
                    "value": 24,
                    "detail": "The agent can reason over some real-estate context, but not yet over a connected national property graph."
                },
            ],
        },
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
