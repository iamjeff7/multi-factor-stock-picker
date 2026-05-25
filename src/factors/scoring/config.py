"""Factor scoring configuration."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from factors.scoring.enums import (
    ScoringMethod,
    ScoringMissingDataPolicy,
    TieMethod,
)


class ScoreRange(BaseModel):
    min: Decimal = Decimal("0.0")
    max: Decimal = Decimal("1.0")

    @model_validator(mode="after")
    def validate_bounds(self) -> ScoreRange:
        if self.min >= self.max:
            raise ValueError("score_range.min must be less than score_range.max")
        return self


class WinsorizeConfig(BaseModel):
    lower_pct: Decimal = Field(default=Decimal("0.01"), ge=Decimal("0"), le=Decimal("1"))
    upper_pct: Decimal = Field(default=Decimal("0.99"), ge=Decimal("0"), le=Decimal("1"))

    @model_validator(mode="after")
    def validate_percentiles(self) -> WinsorizeConfig:
        if self.lower_pct >= self.upper_pct:
            raise ValueError("winsorize.lower_pct must be less than winsorize.upper_pct")
        return self


class FactorScoringConfig(BaseModel):
    scoring_method: ScoringMethod = ScoringMethod.PERCENTILE_RANK
    score_range: ScoreRange = Field(default_factory=ScoreRange)
    tie_method: TieMethod = TieMethod.AVERAGE_RANK
    missing_data_policy: ScoringMissingDataPolicy = ScoringMissingDataPolicy.EXCLUDE_SECURITY
    minimum_security_count: int = Field(default=30, ge=1)
    winsorize: WinsorizeConfig | None = None
