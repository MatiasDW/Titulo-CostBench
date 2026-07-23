"""Persistence models for Scloda traces and knowledge retrieval."""

from datetime import datetime
import os

from app.extensiones import db

try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except Exception:
    Vector = None
    PGVECTOR_AVAILABLE = False


EMBEDDING_DIMENSIONS = int(os.getenv("SCLODA_EMBEDDING_DIMENSIONS", "1536"))


class SclodaTrace(db.Model):
    """Persistent record of a Scloda interaction for observability."""

    __tablename__ = "scloda_traces"

    id = db.Column(db.Integer, primary_key=True)
    trace_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    request_kind = db.Column(db.String(32), nullable=False, default="chat")
    task_type = db.Column(db.String(40), nullable=True, index=True)
    user_message = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text, nullable=True)
    history_count = db.Column(db.Integer, nullable=False, default=0)
    screening_reason = db.Column(db.String(64), nullable=True)
    guardrail_action = db.Column(db.String(64), nullable=True)
    response_status = db.Column(db.String(32), nullable=False, default="ok")
    confidence = db.Column(db.String(16), nullable=True)
    error_code = db.Column(db.String(120), nullable=True)
    model_requested = db.Column(db.String(120), nullable=True)
    model_resolved = db.Column(db.String(120), nullable=True)
    embedding_model = db.Column(db.String(120), nullable=True)
    judge_model = db.Column(db.String(120), nullable=True)
    tools_used = db.Column(db.JSON, nullable=False, default=list)
    tool_payloads = db.Column(db.JSON, nullable=False, default=list)
    retrieved_chunks = db.Column(db.JSON, nullable=False, default=list)
    judge_summary = db.Column(db.JSON, nullable=True)
    prompt_tokens = db.Column(db.Integer, nullable=False, default=0)
    completion_tokens = db.Column(db.Integer, nullable=False, default=0)
    total_tokens = db.Column(db.Integer, nullable=False, default=0)
    latency_ms = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    user = db.relationship("User", backref=db.backref("scloda_traces", lazy=True))

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "request_kind": self.request_kind,
            "task_type": self.task_type,
            "user_message": self.user_message,
            "response_text": self.response_text,
            "history_count": self.history_count,
            "screening_reason": self.screening_reason,
            "guardrail_action": self.guardrail_action,
            "response_status": self.response_status,
            "confidence": self.confidence,
            "error_code": self.error_code,
            "model_requested": self.model_requested,
            "model_resolved": self.model_resolved,
            "embedding_model": self.embedding_model,
            "judge_model": self.judge_model,
            "tools_used": self.tools_used or [],
            "tool_payloads": self.tool_payloads or [],
            "retrieved_chunks": self.retrieved_chunks or [],
            "judge_summary": self.judge_summary,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SclodaKnowledgeChunk(db.Model):
    """Retrieval chunk persisted with optional embedding vectors."""

    __tablename__ = "scloda_knowledge_chunks"

    id = db.Column(db.Integer, primary_key=True)
    source_kind = db.Column(db.String(50), nullable=False, index=True)
    source_key = db.Column(db.String(140), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False, default=0)
    content = db.Column(db.Text, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False, unique=True)
    token_estimate = db.Column(db.Integer, nullable=False, default=0)
    embedding = db.Column(db.JSON, nullable=True)
    embedding_vector = (
        db.Column(Vector(EMBEDDING_DIMENSIONS), nullable=True)
        if PGVECTOR_AVAILABLE
        else db.Column(db.JSON, nullable=True)
    )
    embedding_model = db.Column(db.String(120), nullable=True)
    metadata_json = db.Column(db.JSON, nullable=False, default=dict)
    indexed_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    def to_dict(self, *, include_embedding: bool = False) -> dict:
        payload = {
            "id": self.id,
            "source_kind": self.source_kind,
            "source_key": self.source_key,
            "title": self.title,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "content_hash": self.content_hash,
            "token_estimate": self.token_estimate,
            "embedding_model": self.embedding_model,
            "metadata": self.metadata_json or {},
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
        }
        if include_embedding:
            payload["embedding"] = self.embedding
            payload["embedding_vector"] = self.embedding_vector
        return payload


class SclodaReviewQueueItem(db.Model):
    """Human review item created when the agent response needs escalation."""

    __tablename__ = "scloda_review_queue"

    id = db.Column(db.Integer, primary_key=True)
    trace_id = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    status = db.Column(db.String(24), nullable=False, default="pending", index=True)
    priority = db.Column(db.String(16), nullable=False, default="medium", index=True)
    reason = db.Column(db.String(80), nullable=False)
    task_type = db.Column(db.String(40), nullable=True)
    model_resolved = db.Column(db.String(120), nullable=True)
    assignee_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )
    assignment_note = db.Column(db.Text, nullable=True)
    assigned_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notification_status = db.Column(db.String(24), nullable=False, default="queued")
    notification_channel = db.Column(db.String(24), nullable=False, default="in_app")
    notification_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    user_message = db.Column(db.Text, nullable=False)
    agent_response = db.Column(db.Text, nullable=True)
    reviewer_notes = db.Column(db.Text, nullable=True)
    resolution_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("scloda_review_items", lazy=True),
    )
    assignee = db.relationship(
        "User",
        foreign_keys=[assignee_user_id],
        backref=db.backref("assigned_scloda_reviews", lazy=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "status": self.status,
            "priority": self.priority,
            "reason": self.reason,
            "task_type": self.task_type,
            "model_resolved": self.model_resolved,
            "assignee_user_id": self.assignee_user_id,
            "assignee_email": self.assignee.email if self.assignee else None,
            "assignment_note": self.assignment_note,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "notification_status": self.notification_status,
            "notification_channel": self.notification_channel,
            "notification_sent_at": (
                self.notification_sent_at.isoformat()
                if self.notification_sent_at
                else None
            ),
            "user_message": self.user_message,
            "agent_response": self.agent_response,
            "reviewer_notes": self.reviewer_notes,
            "resolution_summary": self.resolution_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class SclodaCapabilityNode(db.Model):
    """Capability map node for the Quantum Lab / Scloda roadmap."""

    __tablename__ = "scloda_capability_nodes"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    parent_slug = db.Column(db.String(80), nullable=True, index=True)
    label = db.Column(db.String(160), nullable=False)
    domain = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="planned")
    maturity_score = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=False)
    metadata_json = db.Column(db.JSON, nullable=False, default=dict)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "parent_slug": self.parent_slug,
            "label": self.label,
            "domain": self.domain,
            "status": self.status,
            "maturity_score": self.maturity_score,
            "description": self.description,
            "metadata": self.metadata_json or {},
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
