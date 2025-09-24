import hashlib
from typing import Any

def create_document_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()

def _safe_get_score_and_metadata(result_item: Any):
    score = None
    metadata = {}
    try:
        if hasattr(result_item, "score"):
            score = getattr(result_item, "score")
        elif isinstance(result_item, dict) and "score" in result_item:
            score = result_item.get("score")

        if hasattr(result_item, "metadata"):
            metadata = getattr(result_item, "metadata") or {}
        elif isinstance(result_item, dict) and "metadata" in result_item:
            metadata = result_item.get("metadata") or {}
    except Exception:
        score = score or 0
        metadata = metadata or {}

    try:
        score = float(score) if score is not None else 0.0
    except Exception:
        score = 0.0

    if metadata is None:
        metadata = {}

    return score, metadata
