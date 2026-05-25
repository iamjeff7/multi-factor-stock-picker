"""Experiment report generator tests."""

from decimal import Decimal
from pathlib import Path

from backtest.experiment_state import ExperimentRunResult, StockRunResult
from core.types import ExperimentId, SecurityId, Ticker
from reporting.generators.experiment_report import ExperimentReportGenerator
from schemas.results import ExperimentSummaryRecord, StockSummaryRecord


def test_experiment_report_generator_writes_json(tmp_path: Path) -> None:
    experiment_id = ExperimentId("exp_report001")
    result = ExperimentRunResult(
        experiment_id=experiment_id,
        stock_results=[
            StockRunResult(
                security_id=SecurityId("SEC_AAPL"),
                ticker=Ticker("AAPL"),
                status="completed",
                total_return=Decimal("0.12"),
                number_of_trades=3,
            )
        ],
        stock_summaries=[
            StockSummaryRecord(
                experiment_id=experiment_id,
                security_id=SecurityId("SEC_AAPL"),
                ticker=Ticker("AAPL"),
                number_of_trades=3,
                closed_trades=3,
                open_trades=0,
                total_net_pnl=Decimal("1200"),
            )
        ],
        experiment_summary=ExperimentSummaryRecord(
            experiment_id=experiment_id,
            securities_requested=1,
            securities_completed=1,
            securities_skipped=0,
            mean_stock_return=Decimal("0.12"),
            number_of_trades=3,
            total_net_pnl=Decimal("1200"),
        ),
    )

    report_path = ExperimentReportGenerator().generate(
        result,
        experiment_name="test_experiment",
        output_dir=tmp_path,
    )

    assert report_path.exists()
    payload = report_path.read_text(encoding="utf-8")
    assert "trade_metrics" in payload
    assert "experiment_metrics" in payload
    assert "SEC_AAPL" in payload
