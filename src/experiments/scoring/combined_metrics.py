"""Combined strategy metrics and composite scoring."""

from __future__ import annotations

import statistics
from decimal import Decimal

from pydantic import BaseModel

from experiments.ranking import percentile_rank
from experiments.scoring.weights import (
    COMBINED_HIGHER_IS_BETTER,
    DEFAULT_COMBINED_METRIC_WEIGHTS,
)


class StrategyMetrics(BaseModel):
    cagr: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    sortino_ratio: Decimal | None = None
    maximum_drawdown: Decimal | None = None
    calmar_ratio: Decimal | None = None
    profit_factor: Decimal | None = None
    expectancy: Decimal | None = None
    turnover_efficiency: Decimal | None = None
    alpha: Decimal | None = None
    beta: Decimal | None = None
    tail_ratio: Decimal | None = None
    robustness_score: Decimal | None = None


def strategy_metrics_to_ranking_dict(metrics: StrategyMetrics) -> dict[str, Decimal | None]:
    return {
        "cagr": metrics.cagr,
        "sharpe_ratio": metrics.sharpe_ratio,
        "sortino_ratio": metrics.sortino_ratio,
        "maximum_drawdown": metrics.maximum_drawdown,
        "calmar_ratio": metrics.calmar_ratio,
        "profit_factor": metrics.profit_factor,
        "expectancy": metrics.expectancy,
        "turnover_efficiency": metrics.turnover_efficiency,
        "alpha": metrics.alpha,
        "beta": metrics.beta,
        "tail_ratio": metrics.tail_ratio,
        "robustness_score": metrics.robustness_score,
    }


def build_strategy_metrics_from_vbt(
    *,
    nested_metrics: dict[str, object],
    robustness_score: Decimal | None = None,
) -> StrategyMetrics:
    risk_adjusted = _section(nested_metrics, "risk_adjusted")
    risk_and_capital = _section(nested_metrics, "risk_and_capital")
    benchmark = _section(nested_metrics, "benchmark_comparison")
    trade_counts = _section(nested_metrics, "trade_counts")

    cagr = _pct_to_decimal(risk_adjusted.get("cagr"))
    total_return = cagr
    turnover_rate = _decimal_or_none(nested_metrics.get("turnover_rate"))
    if turnover_rate is None:
        turnover_rate = _decimal_or_none(trade_counts.get("trade_frequency_per_trading_year"))
    turnover_efficiency = None
    if total_return is not None and turnover_rate is not None and turnover_rate > Decimal("0"):
        turnover_efficiency = total_return / turnover_rate

    return StrategyMetrics(
        cagr=cagr,
        sharpe_ratio=_decimal_or_none(risk_adjusted.get("sharpe_ratio")),
        sortino_ratio=_decimal_or_none(risk_adjusted.get("sortino_ratio")),
        maximum_drawdown=_pct_to_decimal(risk_and_capital.get("max_drawdown")),
        calmar_ratio=_decimal_or_none(risk_adjusted.get("calmar_ratio")),
        profit_factor=_decimal_or_none(risk_adjusted.get("profit_factor")),
        expectancy=_decimal_or_none(risk_and_capital.get("expectancy")),
        turnover_efficiency=turnover_efficiency,
        alpha=_decimal_or_none(benchmark.get("alpha")),
        beta=_decimal_or_none(benchmark.get("beta")),
        tail_ratio=_decimal_or_none(nested_metrics.get("tail_ratio")),
        robustness_score=robustness_score,
    )


def compute_final_strategy_score(
    metrics: StrategyMetrics,
    *,
    peer_metrics: list[StrategyMetrics] | None = None,
    metric_weights: dict[str, Decimal] | None = None,
) -> Decimal:
    weights = metric_weights or DEFAULT_COMBINED_METRIC_WEIGHTS
    raw = strategy_metrics_to_ranking_dict(metrics)
    peers = [strategy_metrics_to_ranking_dict(row) for row in (peer_metrics or [metrics])]
    if not peer_metrics:
        peers = [raw]

    percentile_ranks: dict[str, Decimal] = {}
    for metric_name in weights:
        values = [
            row[metric_name]
            for row in peers + [raw]
            if row.get(metric_name) is not None
        ]
        current = raw.get(metric_name)
        direction = COMBINED_HIGHER_IS_BETTER.get(metric_name, True)
        if current is None or not values:
            percentile_ranks[metric_name] = Decimal("0.5")
            continue
        percentile_ranks[metric_name] = percentile_rank(
            current,
            values,
            higher_is_better=direction,
        )

    return sum(
        (weights[name] * percentile_ranks[name] for name in weights),
        Decimal("0"),
    )


def aggregate_strategy_metrics(rows: list[StrategyMetrics]) -> StrategyMetrics:
    if not rows:
        return StrategyMetrics()

    def mean_field(name: str) -> Decimal | None:
        values = [getattr(row, name) for row in rows if getattr(row, name) is not None]
        if not values:
            return None
        return Decimal(str(statistics.fmean([float(value) for value in values])))

    drawdowns = [row.maximum_drawdown for row in rows if row.maximum_drawdown is not None]
    return StrategyMetrics(
        cagr=mean_field("cagr"),
        sharpe_ratio=mean_field("sharpe_ratio"),
        sortino_ratio=mean_field("sortino_ratio"),
        maximum_drawdown=min(drawdowns) if drawdowns else None,
        calmar_ratio=mean_field("calmar_ratio"),
        profit_factor=mean_field("profit_factor"),
        expectancy=mean_field("expectancy"),
        turnover_efficiency=mean_field("turnover_efficiency"),
        alpha=mean_field("alpha"),
        beta=mean_field("beta"),
        tail_ratio=mean_field("tail_ratio"),
        robustness_score=mean_field("robustness_score"),
    )


def _section(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if isinstance(value, dict):
        return value
    return {}


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _pct_to_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)) / Decimal("100")
