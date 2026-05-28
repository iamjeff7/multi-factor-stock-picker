"""Default metric weights for experiment composite scores."""

from __future__ import annotations

from decimal import Decimal

DEFAULT_ENTRY_METRIC_WEIGHTS: dict[str, Decimal] = {
    "forward_return": Decimal("0.40"),
    "information_coefficient": Decimal("0.20"),
    "hit_rate": Decimal("0.15"),
    "sharpe_ratio": Decimal("0.10"),
    "maximum_drawdown": Decimal("0.05"),
    "turnover_efficiency": Decimal("0.05"),
    "robustness_score": Decimal("0.05"),
}

DEFAULT_EXIT_METRIC_WEIGHTS: dict[str, Decimal] = {
    "trade_return_improvement": Decimal("0.35"),
    "profit_capture_ratio": Decimal("0.20"),
    "maximum_drawdown_reduction": Decimal("0.15"),
    "win_rate": Decimal("0.10"),
    "average_holding_period_efficiency": Decimal("0.10"),
    "sharpe_ratio_improvement": Decimal("0.05"),
    "robustness_score": Decimal("0.05"),
}

DEFAULT_COMBINED_METRIC_WEIGHTS: dict[str, Decimal] = {
    "cagr": Decimal("0.20"),
    "sharpe_ratio": Decimal("0.15"),
    "sortino_ratio": Decimal("0.10"),
    "maximum_drawdown": Decimal("0.10"),
    "calmar_ratio": Decimal("0.10"),
    "profit_factor": Decimal("0.08"),
    "expectancy": Decimal("0.07"),
    "turnover_efficiency": Decimal("0.05"),
    "alpha": Decimal("0.05"),
    "beta": Decimal("0.03"),
    "tail_ratio": Decimal("0.03"),
    "robustness_score": Decimal("0.04"),
}

ENTRY_HIGHER_IS_BETTER: dict[str, bool] = {
    "forward_return": True,
    "information_coefficient": True,
    "hit_rate": True,
    "sharpe_ratio": True,
    "maximum_drawdown": False,
    "turnover_efficiency": True,
    "robustness_score": True,
}

EXIT_HIGHER_IS_BETTER: dict[str, bool] = {
    "trade_return_improvement": True,
    "profit_capture_ratio": True,
    "maximum_drawdown_reduction": True,
    "win_rate": True,
    "average_holding_period_efficiency": True,
    "sharpe_ratio_improvement": True,
    "robustness_score": True,
}

COMBINED_HIGHER_IS_BETTER: dict[str, bool] = {
    "cagr": True,
    "sharpe_ratio": True,
    "sortino_ratio": True,
    "maximum_drawdown": False,
    "calmar_ratio": True,
    "profit_factor": True,
    "expectancy": True,
    "turnover_efficiency": True,
    "alpha": True,
    "beta": False,
    "tail_ratio": True,
    "robustness_score": True,
}
