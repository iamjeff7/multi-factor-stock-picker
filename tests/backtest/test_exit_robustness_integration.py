"""Partial exit robustness builder tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backtest.exit_robustness import compute_partial_exit_robustness
from core.types import ExperimentId, SecurityId, SignalId, Ticker, TradeId
from research.sample_split import compute_sample_split
from schemas.results import TradeRecord


def _trade(
    *,
    trade_id: str,
    exit_date: date,
    net_pnl: str,
    return_pct: str,
    holding_days: int,
) -> TradeRecord:
    return TradeRecord(
        experiment_id=ExperimentId("exp_test"),
        trade_id=TradeId(trade_id),
        security_id=SecurityId("SEC_AAPL"),
        ticker=Ticker("AAPL"),
        entry_date=date(2020, 1, 2),
        entry_price=Decimal("100"),
        exit_date=exit_date,
        exit_price=Decimal("110"),
        shares=Decimal("10"),
        net_pnl=Decimal(net_pnl),
        return_pct=Decimal(return_pct),
        holding_days=holding_days,
    )


def test_compute_partial_exit_robustness_scores_trade_dimensions() -> None:
    trading_days = [date(2020, 1, d) for d in range(2, 12)]
    split = compute_sample_split(
        trading_days,
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 11),
    )
    trades = [
        _trade(
            trade_id="trade_is_win",
            exit_date=date(2020, 1, 3),
            net_pnl="100",
            return_pct="0.10",
            holding_days=5,
        ),
        _trade(
            trade_id="trade_is_loss",
            exit_date=date(2020, 1, 4),
            net_pnl="-40",
            return_pct="-0.04",
            holding_days=10,
        ),
        _trade(
            trade_id="trade_oos_win",
            exit_date=date(2020, 1, 10),
            net_pnl="80",
            return_pct="0.08",
            holding_days=20,
        ),
    ]

    evaluation = compute_partial_exit_robustness(
        trades,
        split=split,
        exit_signal_id=SignalId("momentum_exit_stack"),
    )

    assert evaluation is not None
    assert evaluation.result is not None
    assert evaluation.pending_dimensions == ["parameter_stability", "regime_stability"]
    assert evaluation.result.performance_stability_score > Decimal("0")
    assert evaluation.result.sample_stability_score >= Decimal("0")
    assert Decimal("0") <= evaluation.result.overall_robustness_score <= Decimal("1")
