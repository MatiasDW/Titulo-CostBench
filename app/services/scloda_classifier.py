"""Lightweight text classifier for Scloda scope, safety, and task routing."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.ml.logging_utils import get_logger

logger = get_logger("scloda.classifier")

DATASET_PATH = (
    Path(__file__).parent.parent.parent / "datasets" / "scloda" / "labeled_conversations.jsonl"
)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


def _load_examples() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not DATASET_PATH.exists():
        return rows
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


@lru_cache(maxsize=1)
def _build_models() -> dict[str, Any]:
    examples = _load_examples()
    if not examples or not SKLEARN_AVAILABLE:
        return {}

    texts = [row["text"] for row in examples]
    scope_labels = [row["scope_label"] for row in examples]
    safety_labels = [row["safety_label"] for row in examples]
    task_labels = [row["task_type"] for row in examples]

    def train(labels: list[str]) -> Pipeline:
        return Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=400,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        ).fit(texts, labels)

    return {
        "scope": train(scope_labels),
        "safety": train(safety_labels),
        "task": train(task_labels),
        "dataset_size": len(examples),
    }


def classify_message(text: str) -> dict[str, Any]:
    """Predict task type, scope, and safety labels for a user message."""
    models = _build_models()
    if not models:
        return {
            "scope_label": "in_scope",
            "scope_confidence": 0.5,
            "safety_label": "normal",
            "safety_confidence": 0.5,
            "task_type": "general_explanation",
            "task_confidence": 0.5,
            "dataset_size": 0,
            "model_ready": False,
        }

    result: dict[str, Any] = {"dataset_size": models["dataset_size"], "model_ready": True}
    for key, output_key in (
        ("scope", "scope_label"),
        ("safety", "safety_label"),
        ("task", "task_type"),
    ):
        model = models[key]
        label = model.predict([text])[0]
        confidence = max(model.predict_proba([text])[0])
        result[output_key] = label
        result[f"{key}_confidence"] = round(float(confidence), 4)
    return result


def get_classifier_status() -> dict[str, Any]:
    models = _build_models()
    return {
        "dataset_path": str(DATASET_PATH),
        "dataset_exists": DATASET_PATH.exists(),
        "sklearn_available": SKLEARN_AVAILABLE,
        "model_ready": bool(models),
        "dataset_size": int(models.get("dataset_size", 0) or 0),
    }
