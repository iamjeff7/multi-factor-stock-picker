"""Cross-section factor evaluation orchestration for unified experiments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from backtest.exit_robustness import compute_partial_exit_robustness
from backtest.exit_robustness_models import ExitRobustnessEvaluation
from backtest.factor_evaluation import FactorEvaluationResult, SingleFactorFactorEvaluator
from core.types import ExperimentId, SignalId
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
from evaluation.robustness.classification import classification_to_grade
from evaluation.robustness.enums import RobustnessClassification
from exit_signals.protocols import ExitSignal
from experiments.config import UnifiedExperimentConfig
from experiments.evaluation.config_adapter import (
    resolve_factor_evaluation_settings,
    to_single_factor_config,
)
from experiments.evaluation.report_payloads import (
    build_cross_section_payload,
    build_exit_robustness_section_payload,
)
from experiments.evaluation.trade_records import trades_to_records
from experiments.signal_catalog import SignalVariant
from research.sample_split import collect_trading_days_from_data, compute_sample_split
from schemas.backtest import Trade
from schemas.enums import RobustnessGrade


@dataclass(frozen=True)
class EntryCrossSectionResult:
    status: str
    skip_reason: str | None
    factor_evaluation: FactorEvaluationResult | None
    robustness_score: Decimal | None
    robustness_grade: RobustnessGrade | None
    cross_section_payload: dict[str, object]


@dataclass(frozen=True)
class ExitRobustnessEvaluationResult:
    status: str
    skip_reason: str | None
    evaluation: ExitRobustnessEvaluation | None
    robustness_score: Decimal | None
    robustness_grade: RobustnessGrade | None
    exit_robustness_payload: dict[str, object]


class UnifiedFactorEvaluator:
    """Runs spec-aligned analytics for unified entry and exit experiments."""

    def __init__(
        self,
        *,
        factor_evaluator: SingleFactorFactorEvaluator | None = None,
    ) -> None:
        self._factor_evaluator = factor_evaluator or SingleFactorFactorEvaluator()

    def evaluate_entry_variant(
        self,
        *,
        config: UnifiedExperimentConfig,
        data_access: DataAccess,
        variant: SignalVariant,
        entry_signal: EntrySignal,
        exit_horizon_months: int,
        start_date: date,
        end_date: date,
    ) -> EntryCrossSectionResult:
        if not config.factor_evaluation.enabled:
            return _skipped("factor_evaluation disabled in config")

        security_count = len(config.securities)
        if security_count < 2:
            return _skipped("cross-section evaluation requires at least two securities")

        settings = resolve_factor_evaluation_settings(
            config.factor_evaluation,
            security_count=security_count,
            exit_horizon_months=exit_horizon_months,
        )
        if security_count < settings.minimum_security_count:
            return _skipped(
                f"security count {security_count} is below minimum "
                f"{settings.minimum_security_count}"
            )

        security_ids = [security.security_id for security in config.securities]
        trading_days = collect_trading_days_from_data(
            data_access,
            security_ids,
            calendar_start=start_date,
            calendar_end=end_date,
        )
        if not trading_days:
            return _skipped("no trading days available for cross-section evaluation")

        sample_split = compute_sample_split(
            trading_days,
            calendar_start=start_date,
            calendar_end=end_date,
            is_fraction=config.research.is_fraction,
        )

        eval_config = to_single_factor_config(
            config.model_copy(
                update={
                    "start_date": start_date,
                    "end_date": end_date,
                }
            ),
            variant=variant,
            factor_evaluation=settings,
        )

        factor_evaluation, _, _ = self._factor_evaluator.evaluate(
            config=eval_config,
            data_access=data_access,
            entry_signal=entry_signal,
            trading_days=trading_days,
            split=sample_split,
            settings=settings,
        )
        if factor_evaluation is None:
            return _skipped("cross-section scoring produced no factor scores")

        robustness_score, robustness_grade = _resolve_robustness(factor_evaluation)
        return EntryCrossSectionResult(
            status="completed",
            skip_reason=None,
            factor_evaluation=factor_evaluation,
            robustness_score=robustness_score,
            robustness_grade=robustness_grade,
            cross_section_payload=build_cross_section_payload(
                factor_evaluation,
                status="completed",
            ),
        )

    def evaluate_exit_variant(
        self,
        *,
        config: UnifiedExperimentConfig,
        data_access: DataAccess,
        exit_signal: ExitSignal,
        trades: list[Trade],
        start_date: date,
        end_date: date,
        experiment_id: ExperimentId,
    ) -> ExitRobustnessEvaluationResult:
        if not config.exit.compute_robustness:
            return _exit_skipped("exit robustness disabled in config")

        closed_trades = [trade for trade in trades if trade.exit_date is not None]
        if not closed_trades:
            return _exit_skipped("no closed trades available for exit robustness")

        security_ids = [security.security_id for security in config.securities]
        trading_days = collect_trading_days_from_data(
            data_access,
            security_ids,
            calendar_start=start_date,
            calendar_end=end_date,
        )
        if not trading_days:
            return _exit_skipped("no trading days available for exit robustness")

        sample_split = compute_sample_split(
            trading_days,
            calendar_start=start_date,
            calendar_end=end_date,
            is_fraction=config.research.is_fraction,
        )
        trade_records = trades_to_records(closed_trades, experiment_id=experiment_id)
        evaluation = compute_partial_exit_robustness(
            trade_records,
            split=sample_split,
            exit_signal_id=SignalId(exit_signal.metadata.signal_id),
        )
        if evaluation is None or evaluation.result is None:
            return _exit_skipped("exit robustness could not be computed from pooled trades")

        robustness_score = evaluation.result.overall_robustness_score
        classification = RobustnessClassification(evaluation.result.robustness_classification)
        return ExitRobustnessEvaluationResult(
            status="completed",
            skip_reason=None,
            evaluation=evaluation,
            robustness_score=robustness_score,
            robustness_grade=classification_to_grade(classification),
            exit_robustness_payload=build_exit_robustness_section_payload(
                evaluation,
                status="completed",
            ),
        )


def _skipped(reason: str) -> EntryCrossSectionResult:
    return EntryCrossSectionResult(
        status="skipped",
        skip_reason=reason,
        factor_evaluation=None,
        robustness_score=None,
        robustness_grade=None,
        cross_section_payload=build_cross_section_payload(
            None,
            status="skipped",
            skip_reason=reason,
        ),
    )


def _exit_skipped(reason: str) -> ExitRobustnessEvaluationResult:
    return ExitRobustnessEvaluationResult(
        status="skipped",
        skip_reason=reason,
        evaluation=None,
        robustness_score=None,
        robustness_grade=None,
        exit_robustness_payload=build_exit_robustness_section_payload(
            None,
            status="skipped",
            skip_reason=reason,
        ),
    )


def _resolve_robustness(
    factor_evaluation: FactorEvaluationResult,
) -> tuple[Decimal | None, RobustnessGrade | None]:
    robustness = factor_evaluation.entry_robustness
    if robustness is None:
        return None, None
    classification = RobustnessClassification(robustness.robustness_classification)
    return robustness.overall_robustness_score, classification_to_grade(classification)
