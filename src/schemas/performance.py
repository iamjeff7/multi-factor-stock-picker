"""Factor performance result schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from core.enums import SamplePeriod
from core.types import SignalId


class QuantileReturnResult(BaseModel):
    evaluation_date: date
    signal_id: SignalId
    horizon: int
    quantile: int
    security_count: int
    average_return: Decimal


class SpreadResult(BaseModel):
    evaluation_date: date
    signal_id: SignalId
    horizon: int
    top_quantile: int
    bottom_quantile: int
    spread_return: Decimal


class LongShortResult(BaseModel):
    evaluation_date: date
    signal_id: SignalId
    horizon: int
    long_return: Decimal
    short_return: Decimal
    long_short_return: Decimal


class FactorPerformanceSummary(BaseModel):
    signal_id: SignalId
    horizon: int
    sample_period: SamplePeriod = SamplePeriod.FULL
    quantile_count: int
    top_quantile: int
    bottom_quantile: int
    mean_top_return: Decimal
    mean_bottom_return: Decimal
    mean_spread: Decimal
    mean_long_short_return: Decimal
    spread_win_rate: Decimal
    monotonicity_correlation: Decimal | None
    observation_count: int


class FactorPerformanceSampleAnalysis(BaseModel):
    signal_id: SignalId
    horizon: int
    full_summary: FactorPerformanceSummary | None = None
    in_sample_summary: FactorPerformanceSummary
    out_of_sample_summary: FactorPerformanceSummary
