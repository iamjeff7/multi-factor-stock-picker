"""Exit factor ranking metrics vs baseline fixed-period exit."""

from __future__ import annotations

import statistics
from datetime import date
from decimal import Decimal

from experiments.metrics import PerformanceMetrics, compute_performance_metrics
from schemas.backtest import Trade


def build_exit_ranking_metrics(
    *,
    variant_trades: list[Trade],
    baseline_trades: list[Trade],
    trading_days: int,
    calendar_start: date,
    calendar_end: date,
    initial_capital: Decimal,
    closes: dict[date, Decimal],
    robustness_score: Decimal | None,
) -> dict[str, Decimal | None]:
    variant_metrics = compute_performance_metrics(
        variant_trades,
        trading_days=trading_days,
        calendar_start=calendar_start,
        calendar_end=calendar_end,
        initial_capital=initial_capital,
    )
    baseline_metrics = compute_performance_metrics(
        baseline_trades,
        trading_days=trading_days,
        calendar_start=calendar_start,
        calendar_end=calendar_end,
        initial_capital=initial_capital,
    )

    variant_returns = _trade_returns(variant_trades)
    baseline_returns = _trade_returns(baseline_trades)
    trade_return_improvement = _mean_delta(variant_returns, baseline_returns)

    return {
        "trade_return_improvement": trade_return_improvement,
        "profit_capture_ratio": _profit_capture_ratio(variant_trades, closes),
        "maximum_drawdown_reduction": _drawdown_reduction(variant_metrics, baseline_metrics),
        "win_rate": _win_rate(variant_trades),
        "average_holding_period_efficiency": _holding_period_efficiency(variant_trades),
        "sharpe_ratio_improvement": _metric_delta(
            variant_metrics.sharpe_ratio,
            baseline_metrics.sharpe_ratio,
        ),
        "robustness_score": robustness_score,
    }


def exit_metrics_to_ranking_dict(metrics: dict[str, Decimal | None]) -> dict[str, Decimal | None]:
    return dict(metrics)


def _trade_returns(trades: list[Trade]) -> list[Decimal]:
    returns: list[Decimal] = []
    for trade in trades:
        if trade.exit_date is None or trade.entry_price <= Decimal("0"):
            continue
        exit_price = trade.exit_price or trade.entry_price
        returns.append((exit_price / trade.entry_price) - Decimal("1"))
    return returns


def _mean_delta(left: list[Decimal], right: list[Decimal]) -> Decimal | None:
    if not left or not right:
        return None
    left_mean = sum(left, start=Decimal("0")) / Decimal(len(left))
    right_mean = sum(right, start=Decimal("0")) / Decimal(len(right))
    return left_mean - right_mean


def _metric_delta(left: Decimal | None, right: Decimal | None) -> Decimal | None:
    if left is None or right is None:
        return None
    return left - right


def _drawdown_reduction(
    variant: PerformanceMetrics,
    baseline: PerformanceMetrics,
) -> Decimal | None:
    if variant.max_drawdown is None or baseline.max_drawdown is None:
        return None
    return baseline.max_drawdown - variant.max_drawdown


def _win_rate(trades: list[Trade]) -> Decimal | None:
    closed = [trade for trade in trades if trade.exit_date is not None]
    if not closed:
        return None
    wins = sum(1 for trade in closed if (trade.net_pnl or Decimal("0")) > Decimal("0"))
    return Decimal(wins) / Decimal(len(closed))


def _holding_period_efficiency(trades: list[Trade]) -> Decimal | None:
    values: list[Decimal] = []
    for trade in trades:
        if trade.exit_date is None or trade.entry_price <= Decimal("0"):
            continue
        holding_days = trade.holding_days or (trade.exit_date - trade.entry_date).days
        if holding_days <= 0:
            continue
        exit_price = trade.exit_price or trade.entry_price
        trade_return = (exit_price / trade.entry_price) - Decimal("1")
        values.append(trade_return / Decimal(holding_days))
    if not values:
        return None
    return Decimal(str(statistics.fmean([float(value) for value in values])))


def _profit_capture_ratio(trades: list[Trade], closes: dict[date, Decimal]) -> Decimal | None:
    ratios: list[Decimal] = []
    for trade in trades:
        if trade.exit_date is None or trade.entry_price <= Decimal("0"):
            continue
        exit_price = trade.exit_price or trade.entry_price
        realized = (exit_price / trade.entry_price) - Decimal("1")
        peak_price = trade.entry_price
        for day, close in closes.items():
            if trade.entry_date <= day <= trade.exit_date:
                peak_price = max(peak_price, close)
        max_profit = (peak_price / trade.entry_price) - Decimal("1")
        if max_profit <= Decimal("0"):
            ratios.append(Decimal("1") if realized >= Decimal("0") else Decimal("0"))
            continue
        ratios.append(min(Decimal("1"), realized / max_profit))
    if not ratios:
        return None
    return Decimal(str(statistics.fmean([float(value) for value in ratios])))
