"""Tests for trailing stop exit signal."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backtest.experiment_config import SignalConfig
from backtest.signal_factory import build_exit_signal
from core.types import DataVersion, PositionId, SecurityId, Ticker
from exit_signals.composite import CompositeExitSignalImpl
from exit_signals.trailing_stop.trailing_stop import TrailingStopExitSignal
from schemas.data import PriceBar
from schemas.enums import ExitDecision
from schemas.exit import PositionContext


class ClosePriceDataAccess:
    def __init__(self, close_by_date: dict[date, Decimal]) -> None:
        self._close_by_date = close_by_date

    @property
    def data_version(self) -> DataVersion:
        return DataVersion("test_data_001")

    def get_prices(
        self,
        security_id: SecurityId,
        start_date: date,
        end_date: date,
        as_of_date: date,
    ) -> list[PriceBar]:
        del security_id, as_of_date
        return [
            _price_bar(trade_date, close)
            for trade_date, close in self._close_by_date.items()
            if start_date <= trade_date <= end_date
        ]

    def get_fundamentals(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return []

    def get_corporate_actions(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return []

    def get_metadata(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return None

    def get_delisting_info(self, security_id: SecurityId):
        del security_id
        return None

    def list_security_ids(self) -> list[SecurityId]:
        return []


def _price_bar(trade_date: date, close: Decimal) -> PriceBar:
    return PriceBar(
        trade_date=trade_date,
        open=close,
        high=close,
        low=close,
        close=close,
        adjusted_close=close,
        volume=1_000,
    )


def _position(*, highest_price: Decimal = Decimal("120")) -> PositionContext:
    return PositionContext(
        position_id=PositionId("pos_001"),
        security_id=SecurityId("SEC_TEST"),
        ticker=Ticker("TEST"),
        entry_date=date(2020, 1, 2),
        entry_price=Decimal("100"),
        position_size=Decimal("10"),
        holding_period=30,
        highest_price_since_entry=highest_price,
    )


def test_trailing_stop_holds_above_threshold() -> None:
    evaluation_date = date(2020, 2, 1)
    data_access = ClosePriceDataAccess({evaluation_date: Decimal("103")})
    signal = TrailingStopExitSignal(trail_pct=Decimal("0.15"))

    result = signal.evaluate(evaluation_date, _position(), data_access)

    assert result.decision is ExitDecision.HOLD


def test_trailing_stop_exits_when_price_falls_from_peak() -> None:
    evaluation_date = date(2020, 2, 1)
    data_access = ClosePriceDataAccess({evaluation_date: Decimal("101")})
    signal = TrailingStopExitSignal(trail_pct=Decimal("0.15"))

    result = signal.evaluate(evaluation_date, _position(highest_price=Decimal("120")), data_access)

    assert result.decision is ExitDecision.EXIT
    assert result.trigger_reason is not None


def test_signal_factory_builds_momentum_exit_stack() -> None:
    signal = build_exit_signal(
        SignalConfig(
            name="momentum_exit_stack",
            params={"stop_pct": 0.10, "trail_pct": 0.15},
        )
    )

    assert isinstance(signal, CompositeExitSignalImpl)
    assert len(signal.signals) == 2


def test_momentum_exit_stack_exits_on_trailing_stop_before_fixed_stop() -> None:
    evaluation_date = date(2020, 2, 1)
    data_access = ClosePriceDataAccess({evaluation_date: Decimal("101")})
    signal = build_exit_signal(
        SignalConfig(
            name="momentum_exit_stack",
            params={"stop_pct": 0.10, "trail_pct": 0.15},
        )
    )

    result = signal.evaluate(evaluation_date, _position(highest_price=Decimal("120")), data_access)

    assert result.decision is ExitDecision.EXIT
