"""Information coefficient result schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from core.enums import SamplePeriod
from core.types import SecurityId, SignalId


class ForwardReturn(BaseModel):
    evaluation_date: date
    security_id: SecurityId
    horizon: int
    forward_return: Decimal


class DailyICResult(BaseModel):
    evaluation_date: date
    signal_id: SignalId
    horizon: int
    security_count: int
    ic: Decimal


class ICSummary(BaseModel):
    signal_id: SignalId
    horizon: int
    sample_period: SamplePeriod = SamplePeriod.FULL
    mean_ic: Decimal
    median_ic: Decimal
    std_ic: Decimal | None
    ic_information_ratio: Decimal | None
    hit_rate: Decimal
    t_statistic: Decimal | None
    p_value: Decimal | None
    observation_count: int


class ICDegradationMetrics(BaseModel):
    """Derived deltas between in-sample and out-of-sample IC summaries."""

    is_mean_ic: Decimal | None = None
    oos_mean_ic: Decimal | None = None
    is_to_oos_mean_ic_delta: Decimal | None = None
    is_hit_rate: Decimal | None = None
    oos_hit_rate: Decimal | None = None
    is_to_oos_hit_rate_delta: Decimal | None = None
    is_ic_information_ratio: Decimal | None = None
    oos_ic_information_ratio: Decimal | None = None
    overfitting_warning: bool = False


class ICSampleAnalysis(BaseModel):
    """IC summaries and degradation across canonical sample periods."""

    signal_id: SignalId
    horizon: int
    full_summary: ICSummary | None = None
    in_sample_summary: ICSummary
    out_of_sample_summary: ICSummary
    degradation: ICDegradationMetrics
