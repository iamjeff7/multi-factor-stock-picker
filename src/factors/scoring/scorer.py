"""Percentile-rank factor scorer implementation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from factors.scoring.config import FactorScoringConfig
from factors.scoring.enums import ScoringMethod, ScoringMissingDataPolicy
from factors.scoring.preprocessing import winsorize_observations
from factors.scoring.ranking import RankObservation, percentile_rank_scores
from factors.scoring.validator import FactorScoringValidator, is_valid_observation
from schemas.entry import EntrySignalResult
from schemas.enums import SignalDirection
from schemas.factors import FactorScore


class PercentileRankFactorScorer:
    """Normalizes raw entry signal values into cross-sectional factor scores."""

    def __init__(
        self,
        *,
        config: FactorScoringConfig | None = None,
        validator: FactorScoringValidator | None = None,
    ) -> None:
        self._config = config or FactorScoringConfig()
        self._validator = validator or FactorScoringValidator()

    @property
    def config(self) -> FactorScoringConfig:
        return self._config

    def score(
        self,
        raw_signals: Sequence[EntrySignalResult],
        evaluation_date: date,
        *,
        direction: SignalDirection,
        config: FactorScoringConfig | None = None,
    ) -> Sequence[FactorScore]:
        scoring_config = config or self._config
        if scoring_config.scoring_method != ScoringMethod.PERCENTILE_RANK:
            raise ValueError(f"Unsupported scoring method: {scoring_config.scoring_method}")

        self._validator.validate_inputs_or_raise(
            raw_signals,
            evaluation_date,
            direction=direction,
            config=scoring_config,
        )

        valid_observations: list[RankObservation] = []
        missing_rows: list[EntrySignalResult] = []

        for result in raw_signals:
            if is_valid_observation(result.raw_signal_value):
                valid_observations.append(
                    RankObservation(
                        security_id=result.security_id,
                        raw_value=result.raw_signal_value,  # type: ignore[arg-type]
                    )
                )
            else:
                missing_rows.append(result)

        if scoring_config.winsorize is not None:
            valid_observations = winsorize_observations(
                valid_observations,
                scoring_config.winsorize,
            )

        rank_results = percentile_rank_scores(
            valid_observations,
            direction=direction,
            tie_method=scoring_config.tie_method,
            score_range=scoring_config.score_range,
        )

        ranked_by_security = {result.security_id: result for result in raw_signals}
        scores: list[FactorScore] = []

        for observation in valid_observations:
            source = ranked_by_security[observation.security_id]
            rank_result = rank_results[observation.security_id]
            scores.append(
                FactorScore(
                    evaluation_date=evaluation_date,
                    security_id=source.security_id,
                    ticker=source.ticker,
                    signal_id=source.signal_id,
                    raw_signal_value=source.raw_signal_value,
                    factor_rank=rank_result.factor_rank,
                    factor_score=rank_result.factor_score,
                )
            )

        for result in missing_rows:
            assigned = _assign_missing_score(result, evaluation_date, scoring_config)
            if assigned is not None:
                scores.append(assigned)

        scores.sort(key=lambda row: str(row.security_id))
        self._validator.validate_outputs_or_raise(scores, config=scoring_config)
        return scores


def _assign_missing_score(
    result: EntrySignalResult,
    evaluation_date: date,
    config: FactorScoringConfig,
) -> FactorScore | None:
    if config.missing_data_policy == ScoringMissingDataPolicy.EXCLUDE_SECURITY:
        return None
    if config.missing_data_policy == ScoringMissingDataPolicy.ASSIGN_LOWEST_SCORE:
        factor_score = config.score_range.min
    elif config.missing_data_policy == ScoringMissingDataPolicy.ASSIGN_NEUTRAL_SCORE:
        factor_score = (config.score_range.min + config.score_range.max) / Decimal("2")
    else:
        raise ValueError(f"Unsupported missing data policy: {config.missing_data_policy}")

    return FactorScore(
        evaluation_date=evaluation_date,
        security_id=result.security_id,
        ticker=result.ticker,
        signal_id=result.signal_id,
        raw_signal_value=result.raw_signal_value,
        factor_rank=None,
        factor_score=factor_score,
    )
