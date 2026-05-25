"""Information coefficient configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from factors.ic.enums import CorrelationMethod


class ICConfig(BaseModel):
    correlation_method: CorrelationMethod = CorrelationMethod.SPEARMAN
    minimum_security_count: int = Field(default=30, ge=1)
    horizons: list[int] = Field(
        default_factory=lambda: [5, 21, 63, 126, 252],
    )

    @model_validator(mode="after")
    def validate_horizons(self) -> ICConfig:
        if not self.horizons:
            raise ValueError("horizons must contain at least one value")
        if any(horizon < 1 for horizon in self.horizons):
            raise ValueError("horizons must be positive trading-day counts")
        return self
