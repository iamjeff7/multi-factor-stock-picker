"""Build partial exit robustness scores from experiment trade outcomes."""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from decimal import Decimal

from backtest.exit_robustness_models import ExitRobustnessEvaluation
from core.types import SignalId
from evaluation.exit.robustness.components import (
    score_holding_period_stability,
    score_performance_stability,
    score_risk_stability,
    score_sample_stability,
    score_trade_distribution_stability,
)
from evaluation.exit.robustness.config import ExitRobustnessConfig
from evaluation.exit.robustness.sample_inputs import (
    _average_return_pct,
    build_exit_sample_stability_from_split,
)
from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.normalize import quantize_score
from reporting.experiment_aggregators import aggregate_trade_metrics
from research.sample_split import SampleSplit
from schemas.exit_robustness import (
    ExitRobustnessResult,
    HoldingPeriodMetrics,
    HoldingPeriodStabilityInput,
    PerformanceStabilityInput,
    RiskStabilityInput,
    TradeDistributionStabilityInput,
)
from schemas.results import TradeRecord

PENDING_EXIT_ROBUSTNESS_DIMENSIONS = (
    "regime_stability",
    "parameter_stability",
)

ACTIVE_EXIT_ROBUSTNESS_WEIGHT_KEYS = (
    "performance_stability",
    "sample_stability",
    "holding_period_stability",
    "trade_distribution_stability",
    "risk_stability",
)

_HOLDING_PERIOD_BUCKETS: tuple[tuple[str, int, int | None], ...] = (
    ("1_5", 1, 5),
    ("6_20", 6, 20),
    ("21_60", 21, 60),
    ("61_plus", 61, None),
)


def compute_partial_exit_robustness(
    trades: Sequence[TradeRecord],
    *,
    split: SampleSplit,
    exit_signal_id: SignalId,
    config: ExitRobustnessConfig | None = None,
) -> ExitRobustnessEvaluation | None:
    """Score trade-derived exit robustness dimensions; regime and parameter remain pending."""
    closed = [trade for trade in trades if trade.exit_date is not None]
    if not closed:
        return None

    scoring_config = config or ExitRobustnessConfig()
    pending_dimensions = list(PENDING_EXIT_ROBUSTNESS_DIMENSIONS)

    performance_stability = _build_performance_stability(closed)
    if performance_stability is None:
        return None

    sample_stability = build_exit_sample_stability_from_split(closed, split=split)
    holding_period_stability = _build_holding_period_stability(closed)
    if not holding_period_stability.buckets:
        pending_dimensions.append("holding_period_stability")

    trade_distribution_stability = _build_trade_distribution_stability(closed)
    risk_stability = _build_risk_stability(closed)

    performance_stability_score = quantize_score(
        score_performance_stability(performance_stability, config=scoring_config)
    )
    sample_stability_score = quantize_score(
        score_sample_stability(sample_stability, config=scoring_config)
    )
    holding_period_stability_score = quantize_score(
        score_holding_period_stability(holding_period_stability, config=scoring_config)
        if holding_period_stability.buckets
        else Decimal("0")
    )
    trade_distribution_stability_score = quantize_score(
        score_trade_distribution_stability(trade_distribution_stability, config=scoring_config)
    )
    risk_stability_score = quantize_score(
        score_risk_stability(risk_stability, config=scoring_config)
    )

    weights = scoring_config.component_weights
    component_scores = {
        "performance_stability": performance_stability_score,
        "sample_stability": sample_stability_score,
        "holding_period_stability": holding_period_stability_score,
        "trade_distribution_stability": trade_distribution_stability_score,
        "risk_stability": risk_stability_score,
    }
    active_weight = sum(
        getattr(weights, key)
        for key in ACTIVE_EXIT_ROBUSTNESS_WEIGHT_KEYS
        if key not in pending_dimensions
    )
    if active_weight <= Decimal("0"):
        return None

    overall_robustness_score = quantize_score(
        sum(
            component_scores[key] * getattr(weights, key)
            for key in ACTIVE_EXIT_ROBUSTNESS_WEIGHT_KEYS
            if key not in pending_dimensions
        )
        / active_weight
    )
    classification = classify_robustness_score(
        overall_robustness_score,
        thresholds=scoring_config.classification_thresholds,
    )

    return ExitRobustnessEvaluation(
        exit_signal_id=exit_signal_id,
        result=ExitRobustnessResult(
            exit_signal_id=exit_signal_id,
            performance_stability_score=performance_stability_score,
            regime_stability_score=Decimal("0"),
            parameter_stability_score=Decimal("0"),
            holding_period_stability_score=holding_period_stability_score,
            sample_stability_score=sample_stability_score,
            trade_distribution_stability_score=trade_distribution_stability_score,
            risk_stability_score=risk_stability_score,
            overall_robustness_score=overall_robustness_score,
            robustness_classification=classification.value,
        ),
        pending_dimensions=sorted(set(pending_dimensions)),
    )


def _build_performance_stability(
    trades: Sequence[TradeRecord],
) -> PerformanceStabilityInput | None:
    returns = _trade_returns(trades)
    if not returns:
        return None

    _, win_rate, profit_factor, average_trade, _ = aggregate_trade_metrics(trades)
    average_return = sum(returns, start=Decimal("0")) / Decimal(len(returns))
    median_return = Decimal(str(statistics.median(returns)))
    return_std = (
        Decimal(str(statistics.pstdev(returns))) if len(returns) > 1 else Decimal("0")
    )
    return PerformanceStabilityInput(
        average_trade_return=average_return,
        median_trade_return=median_return,
        win_rate=win_rate or Decimal("0"),
        profit_factor=profit_factor or Decimal("0"),
        expectancy=average_trade or Decimal("0"),
        return_volatility=return_std,
    )


def _build_holding_period_stability(
    trades: Sequence[TradeRecord],
) -> HoldingPeriodStabilityInput:
    buckets: list[HoldingPeriodMetrics] = []
    for bucket_name, lower_bound, upper_bound in _HOLDING_PERIOD_BUCKETS:
        bucket_trades = [
            trade
            for trade in trades
            if trade.holding_days is not None
            and trade.holding_days >= lower_bound
            and (upper_bound is None or trade.holding_days <= upper_bound)
        ]
        if not bucket_trades:
            continue
        _, win_rate, profit_factor, _, _ = aggregate_trade_metrics(bucket_trades)
        buckets.append(
            HoldingPeriodMetrics(
                bucket_name=bucket_name,
                average_return=_average_return_pct(bucket_trades),
                win_rate=win_rate or Decimal("0"),
                profit_factor=profit_factor or Decimal("0"),
            )
        )
    return HoldingPeriodStabilityInput(buckets=buckets)


def _build_trade_distribution_stability(
    trades: Sequence[TradeRecord],
) -> TradeDistributionStabilityInput:
    closed = [trade for trade in trades if trade.exit_date is not None]
    winners = [trade for trade in closed if (trade.net_pnl or Decimal("0")) > 0]
    profitable_trade_pct = Decimal(len(winners)) / Decimal(len(closed))

    contributions = [abs(trade.net_pnl or Decimal("0")) for trade in closed]
    total_contribution = sum(contributions, start=Decimal("0"))
    if total_contribution <= Decimal("0"):
        return TradeDistributionStabilityInput(
            profitable_trade_pct=profitable_trade_pct,
            contribution_concentration=Decimal("1"),
            top_trade_contribution_ratio=Decimal("1"),
            largest_winner_contribution=Decimal("1"),
        )

    sorted_contributions = sorted(contributions, reverse=True)
    top_trade_contribution_ratio = sorted_contributions[0] / total_contribution
    herfindahl = sum(
        ((value / total_contribution) ** 2 for value in contributions),
        start=Decimal("0"),
    )
    gross_wins = sum(
        ((trade.net_pnl or Decimal("0")) for trade in winners),
        Decimal("0"),
    )
    largest_winner = max(
        ((trade.net_pnl or Decimal("0")) for trade in winners),
        default=Decimal("0"),
    )
    largest_winner_contribution = (
        largest_winner / gross_wins if gross_wins > Decimal("0") else Decimal("0")
    )
    return TradeDistributionStabilityInput(
        profitable_trade_pct=profitable_trade_pct,
        contribution_concentration=herfindahl,
        top_trade_contribution_ratio=top_trade_contribution_ratio,
        largest_winner_contribution=largest_winner_contribution,
    )


def _build_risk_stability(trades: Sequence[TradeRecord]) -> RiskStabilityInput:
    returns = _trade_returns(trades)
    losses = [value for value in returns if value < Decimal("0")]
    volatility = (
        Decimal(str(statistics.pstdev(returns))) if len(returns) > 1 else Decimal("0")
    )
    trade_loss_std = (
        Decimal(str(statistics.pstdev(losses))) if len(losses) > 1 else Decimal("0")
    )
    tail_risk = abs(min(returns)) if returns else Decimal("0")

    ordered = sorted(
        trades,
        key=lambda trade: trade.exit_date or trade.entry_date,
    )
    cumulative = Decimal("0")
    peak = Decimal("0")
    max_drawdown = Decimal("0")
    for trade in ordered:
        cumulative += trade.net_pnl or Decimal("0")
        peak = max(peak, cumulative)
        if peak > Decimal("0"):
            drawdown = (peak - cumulative) / peak
            max_drawdown = max(max_drawdown, drawdown)

    return RiskStabilityInput(
        max_drawdown=max_drawdown,
        trade_loss_std=trade_loss_std,
        volatility=volatility,
        tail_risk=tail_risk,
    )


def _trade_returns(trades: Sequence[TradeRecord]) -> list[Decimal]:
    returns: list[Decimal] = []
    for trade in trades:
        if trade.return_pct is not None:
            returns.append(trade.return_pct)
            continue
        if (
            trade.net_pnl is not None
            and trade.entry_price > Decimal("0")
            and trade.shares > Decimal("0")
        ):
            cost_basis = trade.entry_price * trade.shares
            returns.append(trade.net_pnl / cost_basis)
    return returns
