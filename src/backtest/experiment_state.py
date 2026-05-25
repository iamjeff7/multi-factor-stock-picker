"""Experiment run result models."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from core.types import ExperimentId, SecurityId, Ticker
from schemas.results import (
    ExperimentSummaryRecord,
    StockSummaryRecord,
    TradeRecord,
)


class StockRunResult(BaseModel):
    security_id: SecurityId
    ticker: Ticker
    status: Literal["completed", "skipped"] = "completed"
    skip_reason: str | None = None
    total_return: Decimal | None = None
    number_of_trades: int = 0
    stock_summary: StockSummaryRecord | None = None


class ExperimentRunResult(BaseModel):
    experiment_id: ExperimentId
    stock_results: list[StockRunResult] = Field(default_factory=list)
    trade_records: list[TradeRecord] = Field(default_factory=list)
    stock_summaries: list[StockSummaryRecord] = Field(default_factory=list)
    experiment_summary: ExperimentSummaryRecord
    report_path: str | None = None

    @property
    def securities_completed(self) -> int:
        return sum(1 for result in self.stock_results if result.status == "completed")

    @property
    def securities_skipped(self) -> int:
        return sum(1 for result in self.stock_results if result.status == "skipped")
