"""Cross-sectional portfolio selection helpers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from core.types import SecurityId
from schemas.factors import FactorScore


def build_top_n_selections(
    factor_scores: Sequence[FactorScore],
    top_n: int,
) -> dict[date, set[SecurityId]]:
    """Map each evaluation date to the top-N security IDs by factor rank."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    by_date: dict[date, list[FactorScore]] = {}
    for row in factor_scores:
        by_date.setdefault(row.evaluation_date, []).append(row)

    selections: dict[date, set[SecurityId]] = {}
    for evaluation_date, rows in by_date.items():
        ranked = sorted(rows, key=lambda row: row.factor_score, reverse=True)
        selections[evaluation_date] = {row.security_id for row in ranked[:top_n]}

    return selections
