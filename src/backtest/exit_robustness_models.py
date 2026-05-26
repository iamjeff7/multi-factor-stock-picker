"""Exit robustness evaluation models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.types import SignalId
from schemas.exit_robustness import ExitRobustnessResult


class ExitRobustnessEvaluation(BaseModel):
    exit_signal_id: SignalId
    result: ExitRobustnessResult | None = None
    pending_dimensions: list[str] = Field(default_factory=list)
