"""Tests for combined strategy scoring."""

from decimal import Decimal

from experiments.scoring.combined_metrics import (
    StrategyMetrics,
    build_strategy_metrics_from_vbt,
    compute_final_strategy_score,
)


def test_build_strategy_metrics_from_vbt_flattens_nested_payload() -> None:
    metrics = build_strategy_metrics_from_vbt(
        nested_metrics={
            "risk_adjusted": {
                "cagr": "12.5",
                "sharpe_ratio": "1.2",
                "sortino_ratio": "1.5",
                "profit_factor": "1.8",
                "calmar_ratio": "0.9",
            },
            "risk_and_capital": {
                "max_drawdown": "-8.0",
                "expectancy": "0.02",
            },
            "benchmark_comparison": {
                "alpha": "0.01",
                "beta": "0.85",
            },
            "trade_counts": {
                "trade_frequency_per_trading_year": "4",
            },
            "tail_ratio": "1.5",
            "turnover_rate": "4",
        },
        robustness_score=Decimal("0.25"),
    )
    assert metrics.cagr == Decimal("0.125")
    assert metrics.maximum_drawdown == Decimal("-0.08")
    assert metrics.turnover_efficiency == Decimal("0.125") / Decimal("4")
    assert metrics.robustness_score == Decimal("0.25")


def test_compute_final_strategy_score_weights_metrics() -> None:
    low = StrategyMetrics(
        cagr=Decimal("0.01"),
        sharpe_ratio=Decimal("0.5"),
        sortino_ratio=Decimal("0.5"),
        maximum_drawdown=Decimal("-0.20"),
        calmar_ratio=Decimal("0.5"),
        profit_factor=Decimal("1.0"),
        expectancy=Decimal("0.01"),
        turnover_efficiency=Decimal("0.01"),
        alpha=Decimal("0.01"),
        beta=Decimal("1.0"),
        tail_ratio=Decimal("1.0"),
        robustness_score=Decimal("0.5"),
    )
    high = StrategyMetrics(
        cagr=Decimal("0.20"),
        sharpe_ratio=Decimal("2.0"),
        sortino_ratio=Decimal("2.0"),
        maximum_drawdown=Decimal("-0.05"),
        calmar_ratio=Decimal("2.0"),
        profit_factor=Decimal("2.0"),
        expectancy=Decimal("0.05"),
        turnover_efficiency=Decimal("0.10"),
        alpha=Decimal("0.05"),
        beta=Decimal("0.5"),
        tail_ratio=Decimal("2.0"),
        robustness_score=Decimal("0.9"),
    )
    low_score = compute_final_strategy_score(low, peer_metrics=[low, high])
    high_score = compute_final_strategy_score(high, peer_metrics=[low, high])
    assert high_score > low_score
