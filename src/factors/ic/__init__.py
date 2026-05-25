"""Information coefficient analysis."""

from factors.ic.aggregates import summarize_forward_returns, summarize_ic_series
from factors.ic.calculator import SpearmanICCalculator
from factors.ic.config import ICConfig
from factors.ic.enums import CorrelationMethod
from factors.ic.forward_returns import ForwardReturnCalculator, build_trading_calendar
from factors.ic.protocols import InformationCoefficientCalculator
from factors.ic.sample_analysis import (
    analyze_ic_by_sample,
    compute_ic_degradation,
    filter_daily_ic_by_period,
    filter_forward_returns_by_period,
)
from factors.ic.validator import ICValidator

__all__ = [
    "CorrelationMethod",
    "ForwardReturnCalculator",
    "ICConfig",
    "ICValidator",
    "InformationCoefficientCalculator",
    "SpearmanICCalculator",
    "analyze_ic_by_sample",
    "build_trading_calendar",
    "compute_ic_degradation",
    "filter_daily_ic_by_period",
    "filter_forward_returns_by_period",
    "summarize_forward_returns",
    "summarize_ic_series",
]
