"""Multi-position per-ticker trade simulation for factor evaluation."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from backtest.calendar import is_rebalance_date, next_trading_day
from core.enums import RebalanceFrequency
from core.types import ConfigurationHash, PositionId, SecurityId, Ticker, TradeId, UniverseVersion
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
from exit_signals.protocols import ExitSignal
from experiments.entry_schedules import (
    collect_bottom_entry_dates,
    collect_scheduled_entry_dates,
    load_price_bars,
)
from experiments.enums import EntryCadence, EntryEvaluationMode, ExitEvaluationMode
from experiments.exit_schedules import (
    best_within_period_exit_date,
    build_close_lookup,
    entry_execution_day,
    fixed_period_exit_date,
)
from experiments.metrics import PerformanceMetrics, compute_performance_metrics
from schemas.backtest import Trade
from schemas.enums import ExitDecision
from schemas.exit import PositionContext
from schemas.universe import UniverseMembership, UniverseMembershipSnapshot, UniverseMetadata

FORWARD_TRADING_DAYS_6M = 126
POSITION_CAPITAL_FRACTION = Decimal("0.20")


def simulate_entry_factor(
    *,
    data_access: DataAccess,
    security_id: SecurityId,
    ticker: Ticker,
    entry_signal: EntrySignal,
    start_date: date,
    end_date: date,
    initial_capital: Decimal,
    exit_mode: ExitEvaluationMode,
    exit_horizon_months: int,
    forward_trading_months: int = 6,
) -> list[Trade]:
    bars = load_price_bars(data_access, security_id, start_date, end_date)
    trading_days = sorted(
        bar.trade_date for bar in bars if start_date <= bar.trade_date <= end_date
    )
    if not trading_days:
        return []

    closes = build_close_lookup(bars)
    entry_dates = _collect_entry_signal_dates(
        entry_signal=entry_signal,
        data_access=data_access,
        security_id=security_id,
        ticker=ticker,
        trading_days=trading_days,
    )
    forward_days = forward_trading_months * 21

    trades: list[Trade] = []
    for signal_day in entry_dates:
        entry_day = entry_execution_day(signal_day, trading_days)
        if entry_day is None or entry_day not in closes:
            continue
        if exit_mode is ExitEvaluationMode.FIXED_PERIOD:
            exit_day = fixed_period_exit_date(
                entry_day,
                trading_days,
                holding_months=exit_horizon_months,
            )
        else:
            exit_day = best_within_period_exit_date(
                entry_day,
                trading_days,
                closes,
                forward_trading_days=forward_days,
            )
        if exit_day is None or exit_day <= entry_day:
            continue
        trade = _build_trade(
            security_id=security_id,
            ticker=ticker,
            entry_day=entry_day,
            exit_day=exit_day,
            closes=closes,
            initial_capital=initial_capital,
        )
        if trade is not None:
            trades.append(trade)
    return trades


def simulate_exit_factor(
    *,
    data_access: DataAccess,
    security_id: SecurityId,
    ticker: Ticker,
    exit_signal: ExitSignal,
    start_date: date,
    end_date: date,
    initial_capital: Decimal,
    entry_mode: EntryEvaluationMode,
    entry_cadence: EntryCadence,
) -> list[Trade]:
    bars = load_price_bars(data_access, security_id, start_date, end_date)
    trading_days = sorted(
        bar.trade_date for bar in bars if start_date <= bar.trade_date <= end_date
    )
    if not trading_days:
        return []

    closes = build_close_lookup(bars)
    if entry_mode is EntryEvaluationMode.FIXED_PERIOD:
        entry_dates = collect_scheduled_entry_dates(trading_days, entry_cadence)
    else:
        entry_dates = collect_bottom_entry_dates(bars, trading_days)

    open_positions: list[_OpenSimPosition] = []
    trades: list[Trade] = []

    for current_day in trading_days:
        close = closes.get(current_day)
        if close is None:
            continue

        for entry_day in entry_dates:
            if entry_day != current_day:
                continue
            exec_day = entry_execution_day(entry_day, trading_days) or entry_day
            exec_close = closes.get(exec_day)
            if exec_close is None:
                continue
            shares = _position_shares(initial_capital, exec_close)
            if shares <= Decimal("0"):
                continue
            open_positions.append(
                _OpenSimPosition(
                    position_id=PositionId(f"pos_{uuid.uuid4().hex[:8]}"),
                    entry_date=exec_day,
                    entry_price=exec_close,
                    shares=shares,
                    highest=exec_close,
                    lowest=exec_close,
                )
            )

        still_open: list[_OpenSimPosition] = []
        for position in open_positions:
            if current_day < position.entry_date:
                still_open.append(position)
                continue
            position.highest = max(position.highest, close)
            position.lowest = min(position.lowest, close)
            context = PositionContext(
                position_id=position.position_id,
                security_id=security_id,
                ticker=ticker,
                entry_date=position.entry_date,
                entry_price=position.entry_price,
                position_size=position.shares,
                holding_period=(current_day - position.entry_date).days,
                highest_price_since_entry=position.highest,
                lowest_price_since_entry=position.lowest,
                unrealized_pnl=(close - position.entry_price) * position.shares,
            )
            result = exit_signal.evaluate(current_day, context, data_access)
            if result.decision is ExitDecision.EXIT:
                exit_day = next_trading_day(trading_days, current_day) or current_day
                exit_price = closes.get(exit_day, close)
                trades.append(
                    _close_position(
                        security_id=security_id,
                        ticker=ticker,
                        position=position,
                        exit_day=exit_day,
                        exit_price=exit_price,
                    )
                )
            else:
                still_open.append(position)
        open_positions = still_open

    for position in open_positions:
        last_day = trading_days[-1]
        trades.append(
            _close_position(
                security_id=security_id,
                ticker=ticker,
                position=position,
                exit_day=last_day,
                exit_price=closes[last_day],
            )
        )
    return trades


def simulate_baseline_exit_factor(
    *,
    data_access: DataAccess,
    security_id: SecurityId,
    ticker: Ticker,
    start_date: date,
    end_date: date,
    initial_capital: Decimal,
    entry_mode: EntryEvaluationMode,
    entry_cadence: EntryCadence,
    baseline_holding_months: int = 3,
) -> list[Trade]:
    """Simulate exits using fixed holding period as the baseline reference."""
    bars = load_price_bars(data_access, security_id, start_date, end_date)
    trading_days = sorted(
        bar.trade_date for bar in bars if start_date <= bar.trade_date <= end_date
    )
    if not trading_days:
        return []

    closes = build_close_lookup(bars)
    if entry_mode is EntryEvaluationMode.FIXED_PERIOD:
        entry_dates = collect_scheduled_entry_dates(trading_days, entry_cadence)
    else:
        entry_dates = collect_bottom_entry_dates(bars, trading_days)

    trades: list[Trade] = []
    for entry_day in entry_dates:
        entry_exec = entry_execution_day(entry_day, trading_days) or entry_day
        if entry_exec not in closes:
            continue
        exit_day = fixed_period_exit_date(
            entry_exec,
            trading_days,
            holding_months=baseline_holding_months,
        )
        if exit_day is None or exit_day <= entry_exec:
            continue
        trade = _build_trade(
            security_id=security_id,
            ticker=ticker,
            entry_day=entry_exec,
            exit_day=exit_day,
            closes=closes,
            initial_capital=initial_capital,
        )
        if trade is not None:
            trades.append(trade)
    return trades


def simulate_combined_strategy(
    *,
    data_access: DataAccess,
    security_id: SecurityId,
    ticker: Ticker,
    entry_signal: EntrySignal,
    exit_signal: ExitSignal,
    start_date: date,
    end_date: date,
    initial_capital: Decimal,
) -> list[Trade]:
    """Run entry signal entries with exit signal management; multi-position per ticker."""
    bars = load_price_bars(data_access, security_id, start_date, end_date)
    trading_days = sorted(
        bar.trade_date for bar in bars if start_date <= bar.trade_date <= end_date
    )
    if not trading_days:
        return []

    closes = build_close_lookup(bars)
    entry_dates = _collect_entry_signal_dates(
        entry_signal=entry_signal,
        data_access=data_access,
        security_id=security_id,
        ticker=ticker,
        trading_days=trading_days,
    )
    entry_date_set = set(entry_dates)

    open_positions: list[_OpenSimPosition] = []
    trades: list[Trade] = []

    for current_day in trading_days:
        close = closes.get(current_day)
        if close is None:
            continue

        if current_day in entry_date_set:
            exec_day = entry_execution_day(current_day, trading_days) or current_day
            exec_close = closes.get(exec_day)
            if exec_close is not None:
                shares = _position_shares(initial_capital, exec_close)
                if shares > Decimal("0"):
                    open_positions.append(
                        _OpenSimPosition(
                            position_id=PositionId(f"pos_{uuid.uuid4().hex[:8]}"),
                            entry_date=exec_day,
                            entry_price=exec_close,
                            shares=shares,
                            highest=exec_close,
                            lowest=exec_close,
                        )
                    )

        still_open: list[_OpenSimPosition] = []
        for position in open_positions:
            if current_day < position.entry_date:
                still_open.append(position)
                continue
            position.highest = max(position.highest, close)
            position.lowest = min(position.lowest, close)
            context = PositionContext(
                position_id=position.position_id,
                security_id=security_id,
                ticker=ticker,
                entry_date=position.entry_date,
                entry_price=position.entry_price,
                position_size=position.shares,
                holding_period=(current_day - position.entry_date).days,
                highest_price_since_entry=position.highest,
                lowest_price_since_entry=position.lowest,
                unrealized_pnl=(close - position.entry_price) * position.shares,
            )
            result = exit_signal.evaluate(current_day, context, data_access)
            if result.decision is ExitDecision.EXIT:
                exit_day = next_trading_day(trading_days, current_day) or current_day
                trades.append(
                    _close_position(
                        security_id=security_id,
                        ticker=ticker,
                        position=position,
                        exit_day=exit_day,
                        exit_price=closes.get(exit_day, close),
                    )
                )
            else:
                still_open.append(position)
        open_positions = still_open

    for position in open_positions:
        last_day = trading_days[-1]
        trades.append(
            _close_position(
                security_id=security_id,
                ticker=ticker,
                position=position,
                exit_day=last_day,
                exit_price=closes[last_day],
            )
        )
    return trades


def trades_to_metrics(
    trades: list[Trade],
    *,
    trading_days: int,
    calendar_start: date,
    calendar_end: date,
    initial_capital: Decimal,
) -> PerformanceMetrics:
    return compute_performance_metrics(
        trades,
        trading_days=trading_days,
        calendar_start=calendar_start,
        calendar_end=calendar_end,
        initial_capital=initial_capital,
    )


class _OpenSimPosition:
    def __init__(
        self,
        *,
        position_id: PositionId,
        entry_date: date,
        entry_price: Decimal,
        shares: Decimal,
        highest: Decimal,
        lowest: Decimal,
    ) -> None:
        self.position_id = position_id
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.shares = shares
        self.highest = highest
        self.lowest = lowest


def _collect_entry_signal_dates(
    *,
    entry_signal: EntrySignal,
    data_access: DataAccess,
    security_id: SecurityId,
    ticker: Ticker,
    trading_days: list[date],
) -> list[date]:
    dates: list[date] = []
    previous: date | None = None
    metadata = UniverseMetadata(
        universe_version=UniverseVersion("eval_001"),
        creation_timestamp=datetime.now(tz=UTC),
        configuration_hash=ConfigurationHash("eval"),
        data_version=data_access.data_version,
    )
    for current in trading_days:
        if not is_rebalance_date(current, previous, RebalanceFrequency.MONTHLY):
            previous = current
            continue
        membership = UniverseMembership(
            evaluation_date=current,
            security_id=security_id,
            ticker=ticker,
            is_member=True,
        )
        snapshot = UniverseMembershipSnapshot(
            evaluation_date=current,
            memberships=[membership],
            metadata=metadata,
        )
        results = entry_signal.calculate(current, snapshot, data_access)
        if results and results[0].raw_signal_value is not None:
            dates.append(current)
        previous = current
    return dates


def _position_shares(initial_capital: Decimal, price: Decimal) -> Decimal:
    if price <= Decimal("0"):
        return Decimal("0")
    dollars = initial_capital * POSITION_CAPITAL_FRACTION
    return (dollars / price).quantize(Decimal("0.0001"))


def _build_trade(
    *,
    security_id: SecurityId,
    ticker: Ticker,
    entry_day: date,
    exit_day: date,
    closes: dict[date, Decimal],
    initial_capital: Decimal,
) -> Trade | None:
    entry_price = closes.get(entry_day)
    exit_price = closes.get(exit_day)
    if entry_price is None or exit_price is None or entry_price <= Decimal("0"):
        return None
    shares = _position_shares(initial_capital, entry_price)
    if shares <= Decimal("0"):
        return None
    gross = (exit_price - entry_price) * shares
    return Trade(
        trade_id=TradeId(f"tr_{uuid.uuid4().hex[:8]}"),
        security_id=security_id,
        ticker=ticker,
        entry_date=entry_day,
        entry_price=entry_price,
        exit_date=exit_day,
        exit_price=exit_price,
        shares=shares,
        gross_pnl=gross,
        net_pnl=gross,
        holding_days=(exit_day - entry_day).days,
    )


def _close_position(
    *,
    security_id: SecurityId,
    ticker: Ticker,
    position: _OpenSimPosition,
    exit_day: date,
    exit_price: Decimal,
) -> Trade:
    gross = (exit_price - position.entry_price) * position.shares
    return Trade(
        trade_id=TradeId(f"tr_{uuid.uuid4().hex[:8]}"),
        security_id=security_id,
        ticker=ticker,
        entry_date=position.entry_date,
        entry_price=position.entry_price,
        exit_date=exit_day,
        exit_price=exit_price,
        shares=position.shares,
        gross_pnl=gross,
        net_pnl=gross,
        holding_days=(exit_day - position.entry_date).days,
    )
