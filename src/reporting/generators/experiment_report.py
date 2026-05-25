"""Experiment report generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from backtest.experiment_state import ExperimentRunResult, StockRunResult
from reporting.layout import ResultLayout
from schemas.results import ExperimentSummaryRecord, StockSummaryRecord, TradeRecord


class ExperimentReportGenerator:
    """Writes the final experiment report artifact."""

    def generate(
        self,
        result: ExperimentRunResult,
        *,
        experiment_name: str,
        output_dir: Path,
    ) -> Path:
        report_path = (
            output_dir
            / str(result.experiment_id)
            / ResultLayout.EXPERIMENT_REPORT
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        payload = build_experiment_report_payload(
            result=result,
            experiment_name=experiment_name,
        )
        report_path.write_text(
            json.dumps(payload, indent=2, default=_json_default),
            encoding="utf-8",
        )
        return report_path


def build_experiment_report_payload(
    *,
    result: ExperimentRunResult,
    experiment_name: str,
) -> dict[str, object]:
    return {
        "experiment_id": str(result.experiment_id),
        "experiment_name": experiment_name,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "trade_metrics": _trade_metrics(result.trade_records),
        "stock_metrics": [_stock_metric(row) for row in result.stock_summaries],
        "experiment_metrics": _experiment_metrics(result.experiment_summary),
        "stock_runs": [_stock_run(row) for row in result.stock_results],
        "source_artifacts": [
            ResultLayout.TRADES_FILE,
            ResultLayout.STOCK_SUMMARIES,
            ResultLayout.EXPERIMENT_SUMMARY,
            ResultLayout.BACKTEST_SUMMARY,
            ResultLayout.EXPERIMENT_REPORT,
        ],
    }


def _trade_metrics(trades: list[TradeRecord]) -> dict[str, object]:
    closed = [trade for trade in trades if trade.exit_date is not None]
    winners = [trade for trade in closed if (trade.net_pnl or Decimal("0")) > 0]
    total_net_pnl = sum(
        ((trade.net_pnl or Decimal("0")) for trade in closed),
        Decimal("0"),
    )
    return {
        "number_of_trades": len(closed),
        "win_rate": str(len(winners) / len(closed)) if closed else None,
        "total_net_pnl": str(total_net_pnl) if closed else None,
    }


def _stock_metric(summary: StockSummaryRecord) -> dict[str, object]:
    return summary.model_dump(mode="json")


def _experiment_metrics(summary: ExperimentSummaryRecord) -> dict[str, object]:
    return summary.model_dump(mode="json")


def _stock_run(result: StockRunResult) -> dict[str, object]:
    return {
        "security_id": str(result.security_id),
        "ticker": str(result.ticker),
        "status": result.status,
        "skip_reason": result.skip_reason,
        "total_return": str(result.total_return) if result.total_return is not None else None,
        "number_of_trades": result.number_of_trades,
    }


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")
