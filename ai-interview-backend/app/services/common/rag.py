"""Small, database-agnostic helpers for hybrid retrieval."""

from collections.abc import Iterable
from typing import Any


def reciprocal_rank_fusion(
    ranked_lists: Iterable[list[dict[str, Any]]],
    *,
    k: int = 60,
    id_key: str = "id",
) -> list[dict[str, Any]]:
    """Merge ranked result lists using Reciprocal Rank Fusion.

    Results keep the first-seen payload and gain a ``retrieval_score`` field.
    Ranks are one-based, as defined by the RRF paper.
    """
    merged: dict[Any, dict[str, Any]] = {}
    scores: dict[Any, float] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            item_id = item.get(id_key)
            if item_id is None:
                continue
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            if item_id not in merged:
                merged[item_id] = dict(item)

    ordered_ids = sorted(scores, key=scores.get, reverse=True)
    result = []
    for item_id in ordered_ids:
        item = merged[item_id]
        item["retrieval_score"] = round(scores[item_id], 8)
        result.append(item)
    return result


def normalize_retrieval_scores(
    items: list[dict[str, Any]],
    *,
    score_key: str,
    output_key: str = "similarity",
) -> list[dict[str, Any]]:
    """Expose ranking scores as a comparable 0-1 relevance value for UI consumers."""
    if not items:
        return items

    maximum = max(float(item.get(score_key) or 0.0) for item in items)
    for item in items:
        score = float(item.get(score_key) or 0.0)
        item[output_key] = round(score / maximum, 4) if maximum > 0 else 0.0
    return items
