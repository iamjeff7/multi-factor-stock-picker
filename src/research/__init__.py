"""Research validation framework (in-sample / out-of-sample)."""

from research.config import ResearchSettings, SampleSplitMetadata
from research.degradation import SampleDegradationMetrics, compute_degradation_metrics
from research.sample_split import (
    SampleSplit,
    classify_date,
    collect_trading_days_from_data,
    compute_sample_split,
    filter_trades_by_period as filter_trades,
    split_to_metadata,
)
from research.validator import validate_research_settings

__all__ = [
    "ResearchSettings",
    "SampleDegradationMetrics",
    "SampleSplit",
    "SampleSplitMetadata",
    "classify_date",
    "collect_trading_days_from_data",
    "compute_degradation_metrics",
    "compute_sample_split",
    "filter_trades",
    "split_to_metadata",
    "validate_research_settings",
]
