"""Weighted-mean factor combiner implementation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from core.types import SecurityId, SignalId
from factors.combination.config import FactorCombinationConfig
from factors.combination.enums import CombinationMethod, MissingFactorPolicy
from factors.combination.ranking import CompositeObservation, average_rank_composite_scores
from factors.combination.validator import FactorCombinationValidator
from schemas.factors import CompositeScore, FactorScore

NEUTRAL_FACTOR_SCORE = Decimal("0.5")
SCORE_QUANTIZE = Decimal("0.0000000001")


class WeightedMeanFactorCombiner:
    """Combines normalized factor scores into composite scores."""

    def __init__(
        self,
        *,
        config: FactorCombinationConfig | None = None,
        validator: FactorCombinationValidator | None = None,
    ) -> None:
        self._config = config or FactorCombinationConfig(
            factor_weights={
                "momentum_12m": Decimal("1"),
                "quality_roe": Decimal("1"),
                "value_pe": Decimal("1"),
            }
        )
        self._validator = validator or FactorCombinationValidator()

    @property
    def config(self) -> FactorCombinationConfig:
        return self._config

    def combine(
        self,
        factor_scores: Sequence[FactorScore],
        evaluation_date: date,
        *,
        config: FactorCombinationConfig | None = None,
    ) -> Sequence[CompositeScore]:
        combination_config = config or self._config
        if combination_config.combination_method != CombinationMethod.WEIGHTED_MEAN:
            raise ValueError(
                f"Unsupported combination method: {combination_config.combination_method}"
            )

        self._validator.validate_inputs_or_raise(
            factor_scores,
            evaluation_date,
            config=combination_config,
        )

        enabled_factors = combination_config.enabled_factors
        normalized_weights = combination_config.normalized_weights()
        scores_by_security = _group_scores_by_security(factor_scores, enabled_factors)

        composite_candidates: list[CompositeScore] = []
        for security_id, security_scores in scores_by_security.items():
            composite = _calculate_composite(
                security_id=security_id,
                security_scores=security_scores,
                evaluation_date=evaluation_date,
                enabled_factors=enabled_factors,
                normalized_weights=normalized_weights,
                config=combination_config,
            )
            if composite is not None:
                composite_candidates.append(composite)

        rank_map = average_rank_composite_scores(
            [
                CompositeObservation(
                    security_id=row.security_id,
                    composite_score=row.composite_score,
                )
                for row in composite_candidates
            ]
        )

        results: list[CompositeScore] = []
        for row in composite_candidates:
            results.append(
                row.model_copy(update={"composite_rank": rank_map[row.security_id]})
            )

        results.sort(key=lambda row: str(row.security_id))
        self._validator.validate_outputs_or_raise(results, config=combination_config)
        return results


def _group_scores_by_security(
    factor_scores: Sequence[FactorScore],
    enabled_factors: tuple[SignalId, ...],
) -> dict[SecurityId, dict[SignalId, FactorScore]]:
    enabled = set(enabled_factors)
    grouped: dict[SecurityId, dict[SignalId, FactorScore]] = defaultdict(dict)

    for row in factor_scores:
        if row.signal_id not in enabled:
            continue
        grouped[row.security_id][row.signal_id] = row

    return grouped


def _calculate_composite(
    *,
    security_id: SecurityId,
    security_scores: dict[SignalId, FactorScore],
    evaluation_date: date,
    enabled_factors: tuple[SignalId, ...],
    normalized_weights: dict[SignalId, Decimal],
    config: FactorCombinationConfig,
) -> CompositeScore | None:
    if not security_scores:
        return None

    ticker = next(iter(security_scores.values())).ticker
    available_factors = [signal_id for signal_id in enabled_factors if signal_id in security_scores]
    missing_factors = [signal_id for signal_id in enabled_factors if signal_id not in security_scores]

    if config.missing_factor_policy == MissingFactorPolicy.EXCLUDE_SECURITY and missing_factors:
        return None

    factor_values: dict[SignalId, Decimal] = {
        signal_id: security_scores[signal_id].factor_score for signal_id in available_factors
    }

    if config.missing_factor_policy == MissingFactorPolicy.ASSIGN_NEUTRAL_SCORE:
        for signal_id in missing_factors:
            factor_values[signal_id] = NEUTRAL_FACTOR_SCORE
        effective_available = len(enabled_factors)
    else:
        effective_available = len(available_factors)

    if not _meets_minimum_coverage(
        available_count=effective_available,
        total_count=len(enabled_factors),
        config=config,
    ):
        return None

    active_weights = {
        signal_id: normalized_weights[signal_id]
        for signal_id in factor_values
    }
    weight_total = sum(active_weights.values(), start=Decimal("0"))
    if weight_total == Decimal("0"):
        return None

    composite_score = _quantize(
        sum(
            active_weights[signal_id] * factor_values[signal_id]
            for signal_id in factor_values
        )
        / weight_total
    )
    contributions = _build_contributions(
        factor_values=factor_values,
        active_weights=active_weights,
        weight_total=weight_total,
        composite_score=composite_score,
    )

    return CompositeScore(
        evaluation_date=evaluation_date,
        security_id=security_id,
        ticker=ticker,
        composite_score=composite_score,
        composite_rank=None,
        factor_contributions_json=contributions,
    )


def _build_contributions(
    *,
    factor_values: dict[SignalId, Decimal],
    active_weights: dict[SignalId, Decimal],
    weight_total: Decimal,
    composite_score: Decimal,
) -> dict[str, Decimal]:
    signal_ids = sorted(factor_values, key=str)
    contributions: dict[str, Decimal] = {}
    remaining = composite_score

    for index, signal_id in enumerate(signal_ids):
        if index == len(signal_ids) - 1:
            contributions[str(signal_id)] = remaining
            continue

        contribution = _quantize(
            active_weights[signal_id] / weight_total * factor_values[signal_id]
        )
        contributions[str(signal_id)] = contribution
        remaining -= contribution

    return contributions


def _meets_minimum_coverage(
    *,
    available_count: int,
    total_count: int,
    config: FactorCombinationConfig,
) -> bool:
    required = (
        config.minimum_factor_coverage_pct * Decimal(total_count)
    ).to_integral_value(rounding=ROUND_CEILING)
    return Decimal(available_count) >= required


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANTIZE, rounding=ROUND_HALF_UP)
