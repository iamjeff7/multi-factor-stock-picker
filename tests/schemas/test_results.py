"""Result schema tests."""

from datetime import UTC, datetime
from decimal import Decimal

from core.types import ExperimentId, SecurityId, Ticker
from schemas.results import (
    ExperimentReportManifest,
    ReportArtifactRecord,
    StockSummaryRecord,
)


def test_stock_summary_record_fields() -> None:
    summary = StockSummaryRecord(
        experiment_id=ExperimentId("exp_001"),
        security_id=SecurityId("SEC_AAPL"),
        ticker=Ticker("AAPL"),
        number_of_trades=3,
        closed_trades=2,
        open_trades=1,
        total_net_pnl=Decimal("150"),
        win_rate=Decimal("0.5"),
    )
    assert summary.closed_trades + summary.open_trades == summary.number_of_trades


def test_report_manifest_round_trip() -> None:
    artifact = ReportArtifactRecord(
        experiment_id=ExperimentId("exp_001"),
        report_id="trades",
        report_type="trade_log",
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        format="parquet",
        relative_path="trades/trades.parquet",
        source_artifacts=["trades/trades.parquet"],
    )
    manifest = ExperimentReportManifest(
        experiment_id=ExperimentId("exp_001"),
        artifacts=[artifact],
    )
    payload = manifest.model_dump(mode="json")
    restored = ExperimentReportManifest.model_validate(payload)
    assert restored.artifacts[0].report_id == "trades"
