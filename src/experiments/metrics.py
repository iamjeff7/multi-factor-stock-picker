"""Performance metrics for factor evaluation experiments."""

from __future__ import annotations

import math
import statistics
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from schemas.backtest import Trade

TRADING_DAYS_PER_YEAR = 252


class PerformanceMetrics(BaseModel):
    total_return: Decimal | None = None
    cagr: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    max_drawdown: Decimal | None = None
    round_trips: int = 0
    trading_days: int = 0
    calendar_months: Decimal | None = None
    trades_per_trading_days: Decimal | None = None
    trades_per_month: Decimal | None = None
    trades_per_trading_year: Decimal | None = None


def calendar_months_between(start: date, end: date) -> Decimal:
    if end < start:
        return Decimal("0")
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    return Decimal(str(max(months, 1)))


def compute_performance_metrics(
    trades: list[Trade],
    *,
    trading_days: int,
    calendar_start: date,
    calendar_end: date,
    initial_capital: Decimal,
    daily_returns: list[float] | None = None,
) -> PerformanceMetrics:
    closed = [trade for trade in trades if trade.exit_date is not None]
    round_trips = len(closed)
    months = calendar_months_between(calendar_start, calendar_end)

    trades_per_trading_days = (
        Decimal(str(round_trips)) / Decimal(str(trading_days)) if trading_days > 0 else None
    )
    trades_per_month = (
        Decimal(str(round_trips)) / months if months > Decimal("0") else None
    )
    trades_per_trading_year = (
        Decimal(str(round_trips))
        * Decimal(str(TRADING_DAYS_PER_YEAR))
        / Decimal(str(trading_days))
        if trading_days > 0
        else None
    )

    total_return = _total_return_from_trades(closed, initial_capital)
    cagr = _cagr(total_return, calendar_start, calendar_end)
    sharpe = _sharpe_ratio(daily_returns) if daily_returns else _sharpe_from_trades(closed)
    max_drawdown = _max_drawdown_from_trades(closed, initial_capital, daily_returns)

    return PerformanceMetrics(
        total_return=total_return,
        cagr=cagr,
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        round_trips=round_trips,
        trading_days=trading_days,
        calendar_months=months,
        trades_per_trading_days=trades_per_trading_days,
        trades_per_month=trades_per_month,
        trades_per_trading_year=trades_per_trading_year,
    )


def aggregate_metrics(metrics_list: list[PerformanceMetrics]) -> PerformanceMetrics:
    if not metrics_list:
        return PerformanceMetrics()

    total_round_trips = sum(item.round_trips for item in metrics_list)
    total_trading_days = metrics_list[0].trading_days
    calendar_months = metrics_list[0].calendar_months

    returns = [item.total_return for item in metrics_list if item.total_return is not None]
    sharpes = [item.sharpe_ratio for item in metrics_list if item.sharpe_ratio is not None]
    drawdowns = [item.max_drawdown for item in metrics_list if item.max_drawdown is not None]

    mean_return = (
        Decimal(str(statistics.fmean([float(value) for value in returns]))) if returns else None
    )

    return PerformanceMetrics(
        total_return=mean_return,
        cagr=mean_return,
        sharpe_ratio=(
            Decimal(str(statistics.fmean([float(value) for value in sharpes]))) if sharpes else None
        ),
        max_drawdown=min(drawdowns) if drawdowns else None,
        round_trips=total_round_trips,
        trading_days=total_trading_days,
        calendar_months=calendar_months,
        trades_per_trading_days=(
            Decimal(str(total_round_trips)) / Decimal(str(total_trading_days))
            if total_trading_days > 0
            else None
        ),
        trades_per_month=(
            Decimal(str(total_round_trips)) / calendar_months
            if calendar_months and calendar_months > Decimal("0")
            else None
        ),
        trades_per_trading_year=(
            Decimal(str(total_round_trips))
            * Decimal(str(TRADING_DAYS_PER_YEAR))
            / Decimal(str(total_trading_days))
            if total_trading_days > 0
            else None
        ),
    )


def metrics_to_ranking_dict(metrics: PerformanceMetrics) -> dict[str, Decimal | None]:
    return {
        "sharpe_ratio": metrics.sharpe_ratio,
        "maximum_drawdown": metrics.max_drawdown,
        "turnover_efficiency": _turnover_efficiency(metrics),
    }


def _turnover_efficiency(metrics: PerformanceMetrics) -> Decimal | None:
    if metrics.total_return is None or metrics.trades_per_trading_year is None:
        return None
    if metrics.trades_per_trading_year <= Decimal("0"):
        return None
    return metrics.total_return / metrics.trades_per_trading_year


DEFAULT_METRIC_WEIGHTS: dict[str, Decimal] = {
    "forward_return": Decimal("0.40"),
    "information_coefficient": Decimal("0.20"),
    "hit_rate": Decimal("0.15"),
    "sharpe_ratio": Decimal("0.10"),
    "maximum_drawdown": Decimal("0.05"),
    "turnover_efficiency": Decimal("0.05"),
    "robustness_score": Decimal("0.05"),
}


def _total_return_from_trades(closed: list[Trade], initial_capital: Decimal) -> Decimal | None:
    if initial_capital <= Decimal("0"):
        return None
    net_pnl = sum(
        ((trade.net_pnl or Decimal("0")) for trade in closed),
        Decimal("0"),
    )
    return net_pnl / initial_capital


def _cagr(total_return: Decimal | None, start: date, end: date) -> Decimal | None:
    if total_return is None:
        return None
    years = (end - start).days / 365.25
    if years <= 0:
        return None
    growth = float(Decimal("1") + total_return)
    if growth <= 0:
        return None
    return Decimal(str(growth ** (1 / years) - 1))


def _sharpe_ratio(daily_returns: list[float] | None) -> Decimal | None:
    if not daily_returns or len(daily_returns) < 2:
        return None
    mean = sum(daily_returns) / len(daily_returns)
    variance = sum((value - mean) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
    std_dev = math.sqrt(variance)
    if std_dev == 0:
        return None
    annualized_mean = mean * TRADING_DAYS_PER_YEAR
    annualized_std = std_dev * math.sqrt(TRADING_DAYS_PER_YEAR)
    return Decimal(str(annualized_mean / annualized_std))


def _sharpe_from_trades(closed: list[Trade]) -> Decimal | None:
    returns: list[float] = []
    for trade in closed:
        if trade.entry_price <= Decimal("0"):
            continue
        exit_price = trade.exit_price or trade.entry_price
        returns.append(float((exit_price / trade.entry_price) - Decimal("1")))
    if len(returns) < 2:
        return None
    return _sharpe_ratio(returns)


def _max_drawdown_from_trades(
    closed: list[Trade],
    initial_capital: Decimal,
    daily_returns: list[float] | None,
) -> Decimal | None:
    if daily_returns:
        equity = float(initial_capital)
        peak = equity
        max_dd = 0.0
        for daily_return in daily_returns:
            equity *= 1.0 + daily_return
            peak = max(peak, equity)
            if peak > 0:
                max_dd = min(max_dd, (equity / peak) - 1.0)
        return Decimal(str(max_dd))

    equity = initial_capital
    peak = initial_capital
    max_drawdown = Decimal("0")
    for trade in sorted(closed, key=lambda row: row.exit_date or row.entry_date):
        equity += trade.net_pnl or Decimal("0")
        peak = max(peak, equity)
        if peak > Decimal("0"):
            drawdown = (equity / peak) - Decimal("1")
            max_drawdown = min(max_drawdown, drawdown)
    return max_drawdown if closed else None
