"""Retrieval layer for Scloda using DB-backed cached embeddings."""

from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import func, text

from app.extensiones import db
from app.ml.logging_utils import get_logger
from app.models.ml import MarkovCombination
from app.models.real_estate import RealEstateMetrics
from app.models.scloda import PGVECTOR_AVAILABLE, SclodaKnowledgeChunk
from app.models.trading import Position, TradeHistory, Wallet
from app.models.user import User
from app.services.scloda_tools import INDICATOR_EXPLANATIONS

logger = get_logger("scloda.memory")

OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"


def _is_configured_secret(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    placeholder_markers = ("tu-", "example", "ejemplo", "aqui", "changeme")
    return not any(marker in normalized for marker in placeholder_markers)


_raw_openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_KEY = _raw_openrouter_key if _is_configured_secret(_raw_openrouter_key) else ""
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "https://costbench.cl")
OPENROUTER_X_TITLE = os.getenv(
    "OPENROUTER_X_TITLE", "CostBench - Scloda Knowledge Index"
)
SCLODA_KNOWLEDGE_ENABLED = os.getenv("SCLODA_ENABLE_KNOWLEDGE_INDEX", "true").lower() == "true"
SCLODA_EMBEDDING_MODEL = os.getenv(
    "SCLODA_EMBEDDING_MODEL", "openai/text-embedding-3-small"
)
SCLODA_EMBEDDING_DIMENSIONS = int(os.getenv("SCLODA_EMBEDDING_DIMENSIONS", "1536"))
SCLODA_KNOWLEDGE_MAX_AGE_MINUTES = int(
    os.getenv("SCLODA_KNOWLEDGE_MAX_AGE_MINUTES", "360")
)
SCLODA_KNOWLEDGE_MAX_CHUNKS = int(os.getenv("SCLODA_KNOWLEDGE_MAX_CHUNKS", "4"))
SCLODA_KNOWLEDGE_BATCH_SIZE = int(os.getenv("SCLODA_KNOWLEDGE_BATCH_SIZE", "16"))
SCLODA_KNOWLEDGE_MAX_REAL_ESTATE_ROWS = int(
    os.getenv("SCLODA_KNOWLEDGE_MAX_REAL_ESTATE_ROWS", "24")
)
SCLODA_KNOWLEDGE_MAX_MARKOV_ROWS = int(
    os.getenv("SCLODA_KNOWLEDGE_MAX_MARKOV_ROWS", "12")
)
SCLODA_KNOWLEDGE_MAX_MACRO_SERIES = int(
    os.getenv("SCLODA_KNOWLEDGE_MAX_MACRO_SERIES", "12")
)
SCLODA_EMBEDDING_TIMEOUT_SECONDS = int(
    os.getenv("SCLODA_EMBEDDING_TIMEOUT", "12")
)

KNOWLEDGE_TRIGGER_KEYWORDS = {
    "database",
    "db",
    "dataset",
    "data",
    "knowledge",
    "schema",
    "table",
    "tables",
    "source",
    "sources",
    "real estate",
    "markov",
    "wallet",
    "portfolio",
    "scloda",
    "costbench",
    "how do you know",
    "where does this come from",
    "from the system",
    "internal",
    "quantum lab",
}


def _ensure_knowledge_table() -> None:
    """Create only the Scloda knowledge table when bootstrapping a fresh DB."""
    SclodaKnowledgeChunk.__table__.create(bind=db.engine, checkfirst=True)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]{2,}", (text or "").lower())


def _estimate_tokens(text: str) -> int:
    return max(1, len((text or "").split()))


def _chunk_text(text: str, max_chars: int = 650) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text or "") if part.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        addition = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(addition) <= max_chars:
            current = addition
            continue
        if current:
            chunks.append(current.strip())
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            for start in range(0, len(paragraph), max_chars):
                piece = paragraph[start : start + max_chars].strip()
                if piece:
                    chunks.append(piece)
            current = ""
    if current:
        chunks.append(current.strip())
    return chunks


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _lexical_score(query: str, content: str) -> float:
    query_terms = _tokenize(query)
    content_terms = _tokenize(content)
    if not query_terms or not content_terms:
        return 0.0
    query_counts = Counter(query_terms)
    content_counts = Counter(content_terms)
    overlap = sum(min(query_counts[key], content_counts[key]) for key in query_counts)
    return overlap / max(len(query_terms), 1)


def _make_embedding_request(texts: list[str]) -> list[list[float]]:
    if not OPENROUTER_API_KEY or not texts:
        return []

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_HTTP_REFERER,
        "X-Title": OPENROUTER_X_TITLE,
    }
    payload = {
        "model": SCLODA_EMBEDDING_MODEL,
        "input": texts,
        "provider": {"allow_fallbacks": True, "data_collection": "deny"},
    }

    timeout = httpx.Timeout(SCLODA_EMBEDDING_TIMEOUT_SECONDS, connect=5.0)
    with httpx.Client(timeout=timeout) as client:
        response = client.post(OPENROUTER_EMBEDDINGS_URL, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
        return [item.get("embedding", []) for item in body.get("data", [])]


def _safe_count(model: db.Model) -> int:
    try:
        return db.session.query(model).count()
    except Exception:
        return 0


def _build_schema_documents() -> list[dict[str, Any]]:
    table_specs = [
        (
            User,
            "users",
            "User accounts, onboarding profile data, risk preferences, and role-based access.",
        ),
        (
            Wallet,
            "wallets",
            "Paper trading wallets with balances, initial capital, and wallet ownership.",
        ),
        (
            Position,
            "positions",
            "Open paper trading positions with asset, direction, quantity, and entry pricing.",
        ),
        (
            TradeHistory,
            "trade_history",
            "Closed paper trading operations with realized P&L and timing history.",
        ),
        (
            RealEstateMetrics,
            "real_estate_metrics",
            "Quant real-estate snapshots for Chilean communes: UF/m2, cap rates, vacancy, and days on market.",
        ),
        (
            MarkovCombination,
            "markov_combinations",
            "Statistical causality and transition matrices used for market regime interpretation.",
        ),
    ]

    docs: list[dict[str, Any]] = []
    for model, key, description in table_specs:
        columns = [f"{column.name} ({column.type})" for column in model.__table__.columns]
        count = _safe_count(model)
        text = (
            f"Table `{key}` purpose: {description}\n\n"
            f"Current row count: {count}.\n\n"
            f"Columns: {', '.join(columns)}."
        )
        docs.append(
            {
                "source_kind": "schema",
                "source_key": f"schema:{key}",
                "title": f"Database schema: {key}",
                "content": text,
                "metadata": {"table": key, "row_count": count},
            }
        )
    return docs


def _build_indicator_documents() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for key, payload in INDICATOR_EXPLANATIONS.items():
        text = (
            f"{payload['name']}.\n\n"
            f"What it is: {payload['what']}\n"
            f"Why it matters: {payload['use']}\n"
            f"Impact in Chile: {payload['impact']}\n"
            f"Practical tip: {payload['tip']}"
        )
        docs.append(
            {
                "source_kind": "indicator_guide",
                "source_key": f"indicator:{key}",
                "title": payload["name"],
                "content": text,
                "metadata": {"indicator": key},
            }
        )
    return docs


def _build_real_estate_documents() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []

    latest_run = db.session.query(func.max(RealEstateMetrics.run_date)).scalar()
    if not latest_run:
        return docs

    latest_rows = (
        RealEstateMetrics.query.filter_by(run_date=latest_run)
        .order_by(RealEstateMetrics.net_cap_rate.desc())
        .all()
    )
    if not latest_rows:
        return docs

    avg_uf = round(sum(float(row.uf_m2) for row in latest_rows) / len(latest_rows), 2)
    avg_net_cap = round(
        sum(float(row.net_cap_rate) for row in latest_rows) / len(latest_rows) * 100, 2
    )
    top_yields = ", ".join(
        f"{row.comuna} ({float(row.net_cap_rate) * 100:.2f}% net cap)"
        for row in latest_rows[:5]
    )
    docs.append(
        {
            "source_kind": "dataset_snapshot",
            "source_key": "real_estate:overview",
            "title": "Real estate dataset overview",
            "content": (
                f"Latest real-estate snapshot as of {latest_run.date().isoformat()}.\n\n"
                f"Rows available: {len(latest_rows)}. Average UF/m2: {avg_uf}. "
                f"Average net cap rate: {avg_net_cap}%.\n\n"
                f"Highest-yield communes in the latest snapshot: {top_yields}."
            ),
            "metadata": {"run_date": latest_run.isoformat(), "rows": len(latest_rows)},
        }
    )

    for row in latest_rows[:SCLODA_KNOWLEDGE_MAX_REAL_ESTATE_ROWS]:
        docs.append(
            {
                "source_kind": "entity_row",
                "source_key": f"real_estate:{row.comuna.lower().replace(' ', '_')}:{row.segment_type.lower()}",
                "title": f"Real estate: {row.comuna} {row.segment_type}",
                "content": (
                    f"{row.comuna} {row.segment_type} segment as of {row.run_date.date().isoformat()}.\n\n"
                    f"UF per m2: {float(row.uf_m2):.2f}. Gross cap rate: {float(row.gross_cap_rate) * 100:.2f}%. "
                    f"Net cap rate: {float(row.net_cap_rate) * 100:.2f}%. Vacancy rate: {float(row.vacancy_rate) * 100:.2f}%. "
                    f"Days on market: {row.days_on_market}."
                ),
                "metadata": {
                    "run_date": row.run_date.isoformat(),
                    "comuna": row.comuna,
                    "segment_type": row.segment_type,
                },
            }
        )

    return docs


def _build_macro_documents() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    rows = db.session.execute(
        text(
            """
            WITH ranked AS (
                SELECT
                    series_id,
                    date,
                    value,
                    source,
                    ROW_NUMBER() OVER (PARTITION BY series_id ORDER BY date DESC) AS rn
                FROM macro_indicators
            )
            SELECT series_id, date, value, source, rn
            FROM ranked
            WHERE rn <= 5
            ORDER BY series_id ASC, rn ASC
            """
        )
    ).mappings().all()
    if not rows:
        return docs

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["series_id"], []).append(row)

    visible_series = sorted(grouped.keys())[:SCLODA_KNOWLEDGE_MAX_MACRO_SERIES]
    docs.append(
        {
            "source_kind": "dataset_snapshot",
            "source_key": "macro:overview",
            "title": "Macro indicators dataset overview",
            "content": (
                f"Macro indicators currently available in CostBench: {', '.join(visible_series)}. "
                f"Series count: {len(grouped)}. Retrieval can answer with stored latest values and short recent history."
            ),
            "metadata": {"series_count": len(grouped)},
        }
    )

    for series_id in visible_series:
        series_rows = grouped[series_id]
        latest = series_rows[0]
        latest_value = float(latest["value"]) if latest["value"] is not None else None
        previous_value = (
            float(series_rows[1]["value"])
            if len(series_rows) > 1 and series_rows[1]["value"] is not None
            else None
        )
        delta = (
            round(latest_value - previous_value, 4)
            if latest_value is not None and previous_value is not None
            else None
        )
        recent_points = ", ".join(
            f"{entry['date']}: {float(entry['value']):.4f}"
            for entry in series_rows
            if entry["value"] is not None
        )
        docs.append(
            {
                "source_kind": "entity_row",
                "source_key": f"macro:{series_id.lower()}",
                "title": f"Macro series: {series_id}",
                "content": (
                    f"{series_id} latest stored observation as of {latest['date']}: "
                    f"{latest_value if latest_value is not None else 'unavailable'}."
                    + (
                        f" Change versus previous stored observation: {delta}."
                        if delta is not None
                        else ""
                    )
                    + f" Recent points: {recent_points}."
                ),
                "metadata": {
                    "series_id": series_id,
                    "latest_date": str(latest["date"]),
                    "latest_value": latest_value,
                    "source": latest["source"],
                },
            }
        )

    return docs


def _build_markov_documents() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    latest_runs = (
        MarkovCombination.query.order_by(MarkovCombination.run_date.desc())
        .limit(SCLODA_KNOWLEDGE_MAX_MARKOV_ROWS)
        .all()
    )
    if not latest_runs:
        return docs

    summaries = []
    for row in latest_runs:
        summaries.append(
            f"{row.predictor} -> {row.target}, p-value {float(row.p_value):.4f}, lag1 correlation {float(row.lag1_correlation):.4f}"
        )

    docs.append(
        {
            "source_kind": "dataset_snapshot",
            "source_key": "markov:latest",
            "title": "Latest Markov relationships",
            "content": (
                "Recent Markov and Granger outputs stored in CostBench.\n\n"
                + "\n".join(summaries)
            ),
            "metadata": {"rows": len(latest_runs)},
        }
    )
    return docs


def _build_system_documents() -> list[dict[str, Any]]:
    return [
        {
            "source_kind": "system",
            "source_key": "system:sources",
            "title": "Scloda data sources",
            "content": (
                "Scloda combines live tool calls and internal knowledge.\n\n"
                "Live numeric sources: Banco Central de Chile for UF and USD/CLP, FRED for commodities, "
                "crypto service for BTC and ETH, and SQL-backed product datasets for real estate and market models.\n\n"
                "Internal knowledge is cached in small chunks so answers can retrieve only the relevant context instead of sending large prompts."
            ),
            "metadata": {"kind": "source_map"},
        }
    ]


def _build_markdown_documents() -> list[dict[str, Any]]:
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    if not docs_dir.exists():
        return []

    docs: list[dict[str, Any]] = []
    for path in sorted(docs_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        docs.append(
            {
                "source_kind": "product_doc",
                "source_key": f"doc:{path.stem}",
                "title": path.stem.replace("_", " ").replace("-", " ").title(),
                "content": content,
                "metadata": {"path": str(path.relative_to(docs_dir.parent))},
            }
        )
    return docs


def _build_knowledge_documents() -> list[dict[str, Any]]:
    return (
        _build_system_documents()
        + _build_markdown_documents()
        + _build_schema_documents()
        + _build_indicator_documents()
        + _build_macro_documents()
        + _build_real_estate_documents()
        + _build_markov_documents()
    )


def should_retrieve_knowledge(user_message: str) -> bool:
    lowered = (user_message or "").lower()
    short_live_data_patterns = (
        "what is the current uf",
        "current uf",
        "uf value",
        "valor de la uf",
        "usd/clp",
        "dollar",
        "precio del oro",
        "price of gold",
        "btc",
        "eth",
    )
    if len(lowered.strip()) < 80 and any(pattern in lowered for pattern in short_live_data_patterns):
        return False
    return any(keyword in lowered for keyword in KNOWLEDGE_TRIGGER_KEYWORDS)


def rebuild_knowledge_index(force: bool = False) -> dict[str, Any]:
    """Recreate Scloda's cached knowledge chunks from current DB state."""
    _ensure_knowledge_table()

    documents = _build_knowledge_documents()
    if not documents:
        return {"status": "empty", "documents": 0, "chunks": 0}

    chunk_specs: list[dict[str, Any]] = []
    for doc in documents:
        for idx, chunk in enumerate(_chunk_text(doc["content"])):
            content_hash = hashlib.sha256(
                f"{doc['source_key']}::{idx}::{chunk}".encode("utf-8")
            ).hexdigest()
            chunk_specs.append(
                {
                    "source_kind": doc["source_kind"],
                    "source_key": doc["source_key"],
                    "title": doc["title"],
                    "chunk_index": idx,
                    "content": chunk,
                    "content_hash": content_hash,
                    "token_estimate": _estimate_tokens(chunk),
                    "metadata_json": doc.get("metadata", {}),
                }
            )

    embeddings: list[list[float]] = []
    if OPENROUTER_API_KEY:
        try:
            for start in range(0, len(chunk_specs), SCLODA_KNOWLEDGE_BATCH_SIZE):
                batch = chunk_specs[start : start + SCLODA_KNOWLEDGE_BATCH_SIZE]
                embeddings.extend(_make_embedding_request([item["content"] for item in batch]))
        except Exception as exc:
            logger.warning("knowledge_embeddings_unavailable", error=str(exc))
            embeddings = []

    indexed_at = datetime.utcnow()
    db.session.query(SclodaKnowledgeChunk).delete()

    rows = []
    for index, spec in enumerate(chunk_specs):
        vector = embeddings[index] if index < len(embeddings) else None
        rows.append(
            SclodaKnowledgeChunk(
                source_kind=spec["source_kind"],
                source_key=spec["source_key"],
                title=spec["title"],
                chunk_index=spec["chunk_index"],
                content=spec["content"],
                content_hash=spec["content_hash"],
                token_estimate=spec["token_estimate"],
                embedding=vector,
                embedding_vector=vector if vector else None,
                embedding_model=SCLODA_EMBEDDING_MODEL if vector else None,
                metadata_json=spec["metadata_json"],
                indexed_at=indexed_at,
            )
        )

    db.session.bulk_save_objects(rows)
    db.session.commit()

    return {
        "status": "ok",
        "documents": len(documents),
        "chunks": len(rows),
        "embedding_model": SCLODA_EMBEDDING_MODEL if embeddings else None,
        "indexed_at": indexed_at.isoformat(),
        "forced": force,
    }


def ensure_knowledge_index_ready() -> dict[str, Any]:
    """Create or refresh the knowledge cache when needed."""
    if not SCLODA_KNOWLEDGE_ENABLED:
        return {"status": "disabled"}

    _ensure_knowledge_table()
    latest_indexed_at = db.session.query(func.max(SclodaKnowledgeChunk.indexed_at)).scalar()
    if not latest_indexed_at:
        return rebuild_knowledge_index(force=True)

    age = datetime.utcnow() - latest_indexed_at.replace(tzinfo=None)
    if age > timedelta(minutes=SCLODA_KNOWLEDGE_MAX_AGE_MINUTES):
        return rebuild_knowledge_index(force=True)

    return {
        "status": "ready",
        "chunks": _safe_count(SclodaKnowledgeChunk),
        "indexed_at": latest_indexed_at.isoformat(),
        "embedding_model": SCLODA_EMBEDDING_MODEL,
    }


def retrieve_knowledge(query: str, limit: int | None = None) -> list[dict[str, Any]]:
    """Return the most relevant knowledge chunks for a user query."""
    if not SCLODA_KNOWLEDGE_ENABLED or not query.strip():
        return []

    ensure_knowledge_index_ready()
    query_embedding: list[float] | None = None
    if OPENROUTER_API_KEY:
        try:
            embedding_batch = _make_embedding_request([query])
            query_embedding = embedding_batch[0] if embedding_batch else None
        except Exception as exc:
            logger.warning("query_embedding_failed", error=str(exc))
            query_embedding = None

    candidate_limit = max(limit or SCLODA_KNOWLEDGE_MAX_CHUNKS, 1) * 4
    rows: list[SclodaKnowledgeChunk] = []
    if query_embedding and PGVECTOR_AVAILABLE:
        try:
            rows = (
                SclodaKnowledgeChunk.query.filter(
                    SclodaKnowledgeChunk.embedding_vector.isnot(None)
                )
                .order_by(
                    SclodaKnowledgeChunk.embedding_vector.cosine_distance(query_embedding)
                )
                .limit(candidate_limit)
                .all()
            )
        except Exception as exc:
            logger.warning("pgvector_query_failed", error=str(exc))
            rows = []

    if not rows:
        rows = SclodaKnowledgeChunk.query.all()
    if not rows:
        return []

    scored: list[dict[str, Any]] = []
    for row in rows:
        lexical = _lexical_score(query, row.content)
        title_lexical = _lexical_score(query, row.title)
        metadata_blob = " ".join(
            str(value).lower()
            for value in (row.metadata_json or {}).values()
            if value is not None
        )
        metadata_lexical = _lexical_score(query, metadata_blob)
        semantic = (
            _cosine_similarity(query_embedding, row.embedding)
            if query_embedding and row.embedding
            else 0.0
        )
        score = semantic * 0.65 + lexical * 0.2 + title_lexical * 0.1 + metadata_lexical * 0.05
        if score <= 0:
            continue
        payload = row.to_dict(include_embedding=False)
        payload["score"] = round(score, 4)
        scored.append(payload)

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: limit or SCLODA_KNOWLEDGE_MAX_CHUNKS]


def get_knowledge_index_status() -> dict[str, Any]:
    """Summarize retrieval index state for admin/debug views."""
    _ensure_knowledge_table()
    total_chunks = _safe_count(SclodaKnowledgeChunk)
    latest_indexed_at = db.session.query(func.max(SclodaKnowledgeChunk.indexed_at)).scalar()
    latest_indexed_at_iso = latest_indexed_at.isoformat() if latest_indexed_at else None
    source_breakdown_rows = (
        db.session.query(
            SclodaKnowledgeChunk.source_kind,
            func.count(SclodaKnowledgeChunk.id),
        )
        .group_by(SclodaKnowledgeChunk.source_kind)
        .all()
    )
    return {
        "enabled": SCLODA_KNOWLEDGE_ENABLED,
        "chunks": total_chunks,
        "embedding_model": SCLODA_EMBEDDING_MODEL,
        "embedding_dimensions": SCLODA_EMBEDDING_DIMENSIONS,
        "latest_indexed_at": latest_indexed_at_iso,
        "has_openrouter_key": bool(OPENROUTER_API_KEY),
        "pgvector_enabled": PGVECTOR_AVAILABLE,
        "source_breakdown": {
            source_kind: count for source_kind, count in source_breakdown_rows
        },
    }
