"""Research validation configuration."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from core.enums import ResearchMode, ResearchPhase, SampleScope


class ResearchSettings(BaseModel):
    """Controls in-sample / out-of-sample validation behavior."""

    research_mode: ResearchMode = ResearchMode.PRODUCTION
    research_phase: ResearchPhase = ResearchPhase.VALIDATION
    sample_scope: SampleScope = SampleScope.FULL
    is_fraction: Decimal = Field(default=Decimal("0.80"))
    calendar_start: date = date(2005, 1, 1)


class SampleSplitMetadata(BaseModel):
    """Persisted audit metadata for the fixed chronological split."""

    method: str = "fixed_chronological"
    basis: str = "trading_days"
    is_fraction: Decimal
    calendar_start: date
    calendar_end: date
    split_date: date
    is_trading_days: int
    oos_trading_days: int
    total_trading_days: int
