"""Build entry robustness inputs that require experiment context."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from typing import TYPE_CHECKING

from backtest.experiment_config import SingleFactorExperimentConfig
from backtest.factor_evaluation_config import FactorEvaluationSettings
from data.protocols import DataAccess
from entry_signals.enums import MissingDataPolicy
from entry_signals.momentum.momentum_6_1 import Momentum6_1EntrySignal
from entry_signals.momentum.momentum_12_1 import Momentum12_1EntrySignal
from entry_signals.momentum.trailing_momentum import TrailingMomentumEntrySignal
from entry_signals.protocols import EntrySignal
from schemas.robustness import ParameterStabilityInput

if TYPE_CHECKING:
    from backtest.factor_evaluation import SingleFactorFactorEvaluator


def build_parameter_stability_input(
    *,
    entry_signal: EntrySignal,
    config: SingleFactorExperimentConfig,
    data_access: DataAccess,
    trading_days: Sequence[date],
    settings: FactorEvaluationSettings,
    horizon: int,
    evaluator: SingleFactorFactorEvaluator | None = None,
) -> ParameterStabilityInput | None:
    """Score mean IC across neighboring momentum lookback variants."""
    variants = _momentum_lookback_variants(entry_signal)
    if variants is None or len(variants) < 2:
        return None

    from backtest.factor_evaluation import SingleFactorFactorEvaluator

    factor_evaluator = evaluator or SingleFactorFactorEvaluator()
    performances: list[Decimal] = []
    for _, variant_signal in variants:
        mean_ic = factor_evaluator.compute_mean_ic(
            config=config,
            data_access=data_access,
            entry_signal=variant_signal,
            trading_days=trading_days,
            settings=settings,
            horizon=horizon,
        )
        if mean_ic is not None:
            performances.append(mean_ic)

    if len(performances) < 2:
        return None
    return ParameterStabilityInput(performances=performances)


def _momentum_lookback_variants(
    entry_signal: EntrySignal,
) -> list[tuple[str, TrailingMomentumEntrySignal]] | None:
    if not isinstance(entry_signal, TrailingMomentumEntrySignal):
        return None

    if not isinstance(entry_signal, (Momentum12_1EntrySignal, Momentum6_1EntrySignal)):
        return None

    missing_data_policy = MissingDataPolicy(str(entry_signal.metadata.missing_data_policy))
    baseline = entry_signal.lookback_days
    lookbacks = sorted(
        {
            max(21, int(Decimal(baseline) * Decimal("0.8"))),
            baseline,
            max(21, int(Decimal(baseline) * Decimal("1.2"))),
        }
    )

    variants: list[tuple[str, TrailingMomentumEntrySignal]] = []
    for lookback_days in lookbacks:
        if isinstance(entry_signal, Momentum12_1EntrySignal):
            variant_signal: TrailingMomentumEntrySignal = Momentum12_1EntrySignal(
                lookback_days=lookback_days,
                skip_days=entry_signal.skip_days,
                missing_data_policy=missing_data_policy,
            )
        else:
            variant_signal = Momentum6_1EntrySignal(
                lookback_days=lookback_days,
                skip_days=entry_signal.skip_days,
                missing_data_policy=missing_data_policy,
            )
        variants.append((f"lookback_{lookback_days}", variant_signal))
    return variants
