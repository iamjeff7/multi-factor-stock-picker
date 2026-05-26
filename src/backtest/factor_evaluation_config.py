"""Factor evaluation settings for single-factor experiments."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class FactorEvaluationSettings(BaseModel):
    """Controls cross-sectional scoring and IC analysis in experiments."""

    enabled: bool = True
    minimum_security_count: int = Field(default=30, ge=1)
    primary_horizon: int = Field(default=63, ge=1)
    horizons: list[int] = Field(default_factory=lambda: [63])
    compute_robustness: bool = True

    @model_validator(mode="after")
    def validate_horizons(self) -> FactorEvaluationSettings:
        if not self.horizons:
            raise ValueError("horizons must contain at least one value")
        if any(horizon < 1 for horizon in self.horizons):
            raise ValueError("horizons must be positive trading-day counts")
        if self.primary_horizon not in self.horizons:
            raise ValueError("primary_horizon must be included in horizons")
        return self
