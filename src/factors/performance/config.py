"""Factor performance configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class FactorPerformanceConfig(BaseModel):
    quantile_count: int = Field(default=5, ge=2)
    top_quantile: int | None = None
    bottom_quantile: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_quantiles(self) -> FactorPerformanceConfig:
        if self.top_quantile is not None and self.top_quantile <= self.bottom_quantile:
            raise ValueError("top_quantile must be greater than bottom_quantile")
        if self.top_quantile is not None and self.top_quantile > self.quantile_count:
            raise ValueError("top_quantile cannot exceed quantile_count")
        if self.bottom_quantile > self.quantile_count:
            raise ValueError("bottom_quantile cannot exceed quantile_count")
        return self

    def resolved_top_quantile(self, effective_quantile_count: int) -> int:
        if self.top_quantile is not None:
            return min(self.top_quantile, effective_quantile_count)
        return effective_quantile_count

    def resolved_bottom_quantile(self, effective_quantile_count: int) -> int:
        return min(self.bottom_quantile, effective_quantile_count)
