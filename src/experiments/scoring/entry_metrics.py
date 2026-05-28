"""Entry factor ranking metrics."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from experiments.metrics import PerformanceMetrics


def build_entry_ranking_metrics(
    *,
    cross_section_payload: dict[str, object],
    trade_metrics: PerformanceMetrics,
    robustness_score: Decimal | None,
) -> dict[str, Decimal | None]:
    factor_ic = _as_dict(cross_section_payload.get("factor_ic"))
    factor_performance = _as_dict(cross_section_payload.get("factor_performance"))

    ic_summary = _as_dict(factor_ic.get("full")) if factor_ic.get("available") else {}
    if not ic_summary and factor_ic.get("sample_metrics"):
        sample_metrics = _as_dict(factor_ic.get("sample_metrics"))
        ic_summary = next(iter(sample_metrics.values()), {})

    performance_summary = _as_dict(factor_performance.get("full"))
    if not performance_summary and factor_performance.get("sample_metrics"):
        sample_metrics = _as_dict(factor_performance.get("sample_metrics"))
        performance_summary = next(iter(sample_metrics.values()), {})

    forward_return = _decimal_or_none(performance_summary.get("mean_top_return"))
    if forward_return is None:
        forward_return = _decimal_or_none(ic_summary.get("mean_ic"))

    turnover_efficiency = _turnover_efficiency(
        total_return=trade_metrics.total_return,
        trades_per_trading_year=trade_metrics.trades_per_trading_year,
    )

    return {
        "forward_return": forward_return,
        "information_coefficient": _decimal_or_none(ic_summary.get("mean_ic")),
        "hit_rate": _decimal_or_none(ic_summary.get("hit_rate")),
        "sharpe_ratio": trade_metrics.sharpe_ratio,
        "maximum_drawdown": trade_metrics.max_drawdown,
        "turnover_efficiency": turnover_efficiency,
        "robustness_score": robustness_score,
    }


def entry_metrics_to_ranking_dict(metrics: dict[str, Decimal | None]) -> dict[str, Decimal | None]:
    return dict(metrics)


def _turnover_efficiency(
    *,
    total_return: Decimal | None,
    trades_per_trading_year: Decimal | None,
) -> Decimal | None:
    if total_return is None or trades_per_trading_year is None:
        return None
    turnover_rate = trades_per_trading_year
    if turnover_rate <= Decimal("0"):
        return None
    return total_return / turnover_rate


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _as_dict(value: Any) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}
