"""Single-stock backtest engine."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from backtest.calendar import is_rebalance_date, next_trading_day, trading_days_between
from backtest.config import SingleStockBacktestConfig
from backtest.entry_policy import EntryPolicy, SignalPresentEntryPolicy
from backtest.execution import NextBarExecutionModel
from backtest.lifecycle import (
    apply_split,
    build_position_context,
    close_trade,
    open_trade,
    queue_order,
    update_position_marks,
)
from backtest.position_sizing import PositionSizer, build_position_sizer
from backtest.state import BacktestRunResult, PendingOrder, PortfolioState
from backtest.statistics import DefaultPerformanceCalculator
from backtest.validator import BacktestValidator
from core.enums import ExperimentStatus, ExperimentType, OrderSide
from core.exceptions import ValidationError
from core.types import (
    ConfigurationHash,
    DataVersion,
    ExperimentId,
    PositionId,
    SecurityId,
    TradeId,
    UniverseVersion,
)
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
from exit_signals.protocols import ExitSignal
from reporting.protocols import ResultStore
from schemas.backtest import EquityCurvePoint, PortfolioSnapshot
from schemas.enums import ExitDecision
from schemas.results import (
    BacktestSummaryRecord,
    EquityCurveRecord,
    ExperimentMetadata,
    PortfolioSnapshotRecord,
    TradeRecord,
)
from schemas.universe import UniverseMembership, UniverseMembershipSnapshot, UniverseMetadata


class SingleStockBacktestEngine:
    """Simulates entries, exits, sizing, and accounting for one security."""

    def __init__(
        self,
        *,
        execution_model: NextBarExecutionModel | None = None,
        position_sizer: PositionSizer | None = None,
        performance_calculator: DefaultPerformanceCalculator | None = None,
        validator: BacktestValidator | None = None,
    ) -> None:
        self._performance_calculator = performance_calculator or DefaultPerformanceCalculator()
        self._validator = validator or BacktestValidator()
        self._execution_model = execution_model
        self._position_sizer = position_sizer

    def run(
        self,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        exit_signal: ExitSignal,
        entry_policy: EntryPolicy | None = None,
        result_store: ResultStore | None = None,
    ) -> BacktestRunResult:
        policy = entry_policy or SignalPresentEntryPolicy()
        execution = self._execution_model or NextBarExecutionModel(
            execution_price=config.execution_price,
            slippage_pct=Decimal(str(config.slippage_pct)),
            commission_pct=Decimal(str(config.commission_pct)),
            commission_per_trade=(
                Decimal(str(config.commission_per_trade))
                if config.commission_per_trade is not None
                else None
            ),
        )
        sizer = self._position_sizer or build_position_sizer(
            config.position_size_method,
            config.fixed_dollar_amount,
        )

        experiment_id = ExperimentId(f"exp_{uuid.uuid4().hex[:12]}")
        initial_capital = Decimal(str(config.initial_capital))
        state = PortfolioState(
            experiment_id=experiment_id,
            initial_capital=initial_capital,
            cash=initial_capital,
            peak_portfolio_value=initial_capital,
        )

        trading_days = self._load_trading_days(data_access, config)
        if not trading_days:
            raise ValidationError("No trading days available in backtest range")

        previous_date: date | None = None
        for current_date in trading_days:
            if state.pending_order and state.pending_order.execution_date == current_date:
                self._execute_pending_order(
                    state=state,
                    config=config,
                    data_access=data_access,
                    execution=execution,
                    sizer=sizer,
                    current_date=current_date,
                )

            self._apply_corporate_actions(state, data_access, config.security_id, current_date)
            self._maybe_force_delist_exit(
                state=state,
                config=config,
                data_access=data_access,
                execution=execution,
                current_date=current_date,
                trading_days=trading_days,
            )

            mark_price = self._get_mark_price(
                data_access, config.security_id, current_date, current_date
            )
            update_position_marks(state, mark_price)

            if state.position is not None and state.pending_order is None:
                self._evaluate_exit(
                    state=state,
                    config=config,
                    data_access=data_access,
                    exit_signal=exit_signal,
                    current_date=current_date,
                    trading_days=trading_days,
                    mark_price=mark_price,
                )

            if (
                state.position is None
                and state.pending_order is None
                and is_rebalance_date(current_date, previous_date, config.rebalance_frequency)
            ):
                self._evaluate_entry(
                    state=state,
                    config=config,
                    data_access=data_access,
                    entry_signal=entry_signal,
                    entry_policy=policy,
                    current_date=current_date,
                    trading_days=trading_days,
                )

            portfolio_value, invested_capital = self._portfolio_values(
                state, mark_price if state.position else None
            )
            self._validator.validate_or_raise(state, portfolio_value, invested_capital)
            self._record_snapshot(state, current_date, portfolio_value, invested_capital)
            previous_date = current_date

        if state.pending_order is not None:
            raise ValidationError(
                f"Unresolved pending order at end of backtest: {state.pending_order}"
            )

        summary = self._performance_calculator.summarize(
            state.trades,
            state.equity_curve,
            initial_capital,
        )
        result = BacktestRunResult(
            experiment_id=experiment_id,
            trades=state.trades,
            snapshots=state.snapshots,
            equity_curve=state.equity_curve,
            positions_closed=len([trade for trade in state.trades if trade.exit_date is not None]),
            final_cash=state.cash,
            final_portfolio_value=state.equity_curve[-1].portfolio_value
            if state.equity_curve
            else state.cash,
        )

        if result_store is not None:
            self._persist_results(
                result_store=result_store,
                config=config,
                data_access=data_access,
                experiment_id=experiment_id,
                result=result,
                summary=summary,
            )

        return result

    def _load_trading_days(
        self,
        data_access: DataAccess,
        config: SingleStockBacktestConfig,
    ) -> list[date]:
        bars = data_access.get_prices(
            security_id=config.security_id,
            start_date=config.start_date,
            end_date=config.end_date,
            as_of_date=config.end_date,
        )
        price_dates = [bar.trade_date for bar in bars]
        return trading_days_between(price_dates, config.start_date, config.end_date)

    def _build_universe_snapshot(
        self,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        evaluation_date: date,
    ) -> UniverseMembershipSnapshot:
        return UniverseMembershipSnapshot(
            evaluation_date=evaluation_date,
            memberships=[
                UniverseMembership(
                    evaluation_date=evaluation_date,
                    security_id=config.security_id,
                    ticker=config.ticker,
                    is_member=True,
                )
            ],
            metadata=UniverseMetadata(
                universe_version=UniverseVersion("single_stock"),
                creation_timestamp=datetime.now(tz=UTC),
                configuration_hash=ConfigurationHash(self._configuration_hash(config)),
                data_version=data_access.data_version,
            ),
        )

    def _evaluate_entry(
        self,
        state: PortfolioState,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        entry_policy: EntryPolicy,
        current_date: date,
        trading_days: list[date],
    ) -> None:
        execution_date = next_trading_day(trading_days, current_date)
        if execution_date is None:
            return

        universe = self._build_universe_snapshot(config, data_access, current_date)
        results = entry_signal.calculate(current_date, universe, data_access)
        signal = next((row for row in results if row.security_id == config.security_id), None)
        if not entry_policy.should_enter(signal):
            return

        queue_order(
            state,
            side=OrderSide.BUY,
            signal_date=current_date,
            execution_date=execution_date,
            trigger_reason="entry_signal",
        )

    def _evaluate_exit(
        self,
        state: PortfolioState,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        exit_signal: ExitSignal,
        current_date: date,
        trading_days: list[date],
        mark_price: Decimal,
    ) -> None:
        if state.position is None:
            return

        execution_date = next_trading_day(trading_days, current_date)
        if execution_date is None:
            return

        position_context = build_position_context(state.position, current_date, mark_price)
        result = exit_signal.evaluate(current_date, position_context, data_access)
        if result.decision is not ExitDecision.EXIT:
            return

        queue_order(
            state,
            side=OrderSide.SELL,
            signal_date=current_date,
            execution_date=execution_date,
            trigger_reason=result.trigger_reason,
        )

    def _execute_pending_order(
        self,
        state: PortfolioState,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        execution: NextBarExecutionModel,
        sizer: PositionSizer,
        current_date: date,
    ) -> None:
        order = state.pending_order
        if order is None:
            return

        if order.side is OrderSide.BUY:
            self._execute_buy(state, config, data_access, execution, sizer, current_date, order)
        else:
            self._execute_sell(state, config, data_access, execution, current_date, order)

        state.pending_order = None

    def _execute_buy(
        self,
        state: PortfolioState,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        execution: NextBarExecutionModel,
        sizer: PositionSizer,
        current_date: date,
        order: PendingOrder,
    ) -> None:
        del order
        fill = execution.get_fill_price(
            data_access,
            config.security_id,
            current_date,
            is_buy=True,
        )
        estimated_commission = execution.calculate_commission(fill.fill_price)
        shares = sizer.size_entry(state.cash, fill, estimated_commission)
        notional = shares * fill.fill_price
        commission = execution.calculate_commission(notional)
        total_cost = notional + commission
        if total_cost > state.cash:
            raise ValidationError("Insufficient cash to execute buy order")

        state.cash -= total_cost
        mark_price = self._get_mark_price(
            data_access, config.security_id, current_date, current_date
        )
        trade_id = TradeId(f"trade_{uuid.uuid4().hex[:10]}")
        position_id = PositionId(f"pos_{uuid.uuid4().hex[:10]}")
        open_trade(
            state=state,
            trade_id=trade_id,
            position_id=position_id,
            security_id=config.security_id,
            ticker=config.ticker,
            entry_date=current_date,
            entry_price=fill.fill_price,
            entry_commission=commission,
            shares=shares,
            mark_price=mark_price,
        )

    def _execute_sell(
        self,
        state: PortfolioState,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        execution: NextBarExecutionModel,
        current_date: date,
        order: PendingOrder,
    ) -> None:
        del order
        if state.position is None:
            raise ValidationError("Cannot execute sell without an open position")

        fill = execution.get_fill_price(
            data_access,
            config.security_id,
            current_date,
            is_buy=False,
        )
        position = state.position
        notional = position.shares * fill.fill_price
        commission = execution.calculate_commission(notional)
        proceeds = notional - commission
        gross_pnl = (fill.fill_price - position.entry_price) * position.shares
        net_pnl = proceeds - (position.entry_price * position.shares + position.entry_commission)

        state.cash += proceeds
        close_trade(
            state=state,
            exit_date=current_date,
            exit_price=fill.fill_price,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
        )

    def _apply_corporate_actions(
        self,
        state: PortfolioState,
        data_access: DataAccess,
        security_id: SecurityId,
        current_date: date,
    ) -> None:
        actions = data_access.get_corporate_actions(security_id, current_date)
        for action in actions:
            if action.action_date != current_date:
                continue
            if action.action_type in {"SPLIT", "REVERSE_SPLIT"} and action.ratio is not None:
                apply_split(state, action.ratio)
            if action.action_type in {"CASH_DIVIDEND", "SPECIAL_DIVIDEND"} and action.amount:
                if state.position is not None:
                    state.cash += action.amount * state.position.shares

    def _maybe_force_delist_exit(
        self,
        state: PortfolioState,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        execution: NextBarExecutionModel,
        current_date: date,
        trading_days: list[date],
    ) -> None:
        if state.position is None or state.pending_order is not None:
            return

        delisting = data_access.get_delisting_info(config.security_id)
        if delisting is None or current_date < delisting.delisting_date:
            return

        execution_date = next_trading_day(trading_days, current_date) or current_date
        queue_order(
            state,
            side=OrderSide.SELL,
            signal_date=current_date,
            execution_date=execution_date,
            trigger_reason=f"delisted:{delisting.delisting_reason}",
        )
        if execution_date == current_date:
            self._execute_pending_order(
                state=state,
                config=config,
                data_access=data_access,
                execution=execution,
                sizer=build_position_sizer(config.position_size_method, config.fixed_dollar_amount),
                current_date=current_date,
            )

    def _get_mark_price(
        self,
        data_access: DataAccess,
        security_id: SecurityId,
        start_date: date,
        as_of_date: date,
    ) -> Decimal:
        bars = data_access.get_prices(
            security_id=security_id,
            start_date=start_date,
            end_date=as_of_date,
            as_of_date=as_of_date,
        )
        if not bars:
            raise ValidationError(f"No mark price available for {security_id} on {as_of_date}")
        return bars[-1].close

    def _portfolio_values(
        self,
        state: PortfolioState,
        mark_price: Decimal | None,
    ) -> tuple[Decimal, Decimal]:
        invested = Decimal("0")
        if state.position is not None and mark_price is not None:
            invested = state.position.shares * mark_price
        return state.cash + invested, invested

    def _record_snapshot(
        self,
        state: PortfolioState,
        current_date: date,
        portfolio_value: Decimal,
        invested_capital: Decimal,
    ) -> None:
        del invested_capital
        state.peak_portfolio_value = max(state.peak_portfolio_value, portfolio_value)
        drawdown = None
        if state.peak_portfolio_value > Decimal("0"):
            drawdown = (portfolio_value / state.peak_portfolio_value) - Decimal("1")

        previous_value = state.equity_curve[-1].portfolio_value if state.equity_curve else None
        daily_return = None
        if previous_value is not None and previous_value > Decimal("0"):
            daily_return = (portfolio_value / previous_value) - Decimal("1")

        cumulative_return = None
        if state.initial_capital > Decimal("0"):
            cumulative_return = (portfolio_value / state.initial_capital) - Decimal("1")

        state.snapshots.append(
            PortfolioSnapshot(
                date=current_date,
                cash=state.cash,
                equity=portfolio_value,
                portfolio_value=portfolio_value,
                drawdown=drawdown,
                number_of_positions=1 if state.position is not None else 0,
            )
        )
        state.equity_curve.append(
            EquityCurvePoint(
                date=current_date,
                portfolio_value=portfolio_value,
                daily_return=daily_return,
                cumulative_return=cumulative_return,
            )
        )

    def _configuration_hash(self, config: SingleStockBacktestConfig) -> str:
        payload = json.dumps(config.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def _persist_results(
        self,
        result_store: ResultStore,
        config: SingleStockBacktestConfig,
        data_access: DataAccess,
        experiment_id: ExperimentId,
        result: BacktestRunResult,
        summary: object,
    ) -> None:
        from schemas.backtest import BacktestSummary

        if not isinstance(summary, BacktestSummary):
            raise ValidationError("Expected BacktestSummary for persistence")

        result_store.create_experiment(
            ExperimentMetadata(
                experiment_id=experiment_id,
                experiment_name=config.experiment_name,
                experiment_type=ExperimentType.SINGLE_FACTOR,
                execution_timestamp=datetime.now(tz=UTC),
                data_version=DataVersion(str(data_access.data_version)),
                universe_version=UniverseVersion("single_stock"),
                configuration_hash=ConfigurationHash(self._configuration_hash(config)),
                framework_version="2.0.0",
                status=ExperimentStatus.COMPLETED,
            )
        )
        result_store.save_trades(
            [
                TradeRecord(
                    experiment_id=experiment_id,
                    trade_id=trade.trade_id,
                    security_id=trade.security_id,
                    ticker=trade.ticker,
                    entry_date=trade.entry_date,
                    entry_price=trade.entry_price,
                    exit_date=trade.exit_date,
                    exit_price=trade.exit_price,
                    shares=trade.shares,
                    gross_pnl=trade.gross_pnl,
                    net_pnl=trade.net_pnl,
                    holding_days=trade.holding_days,
                )
                for trade in result.trades
            ]
        )
        result_store.save_portfolio_snapshots(
            [
                PortfolioSnapshotRecord(
                    experiment_id=experiment_id,
                    date=snapshot.date,
                    cash=snapshot.cash,
                    invested_capital=snapshot.portfolio_value - snapshot.cash,
                    equity=snapshot.equity,
                    portfolio_value=snapshot.portfolio_value,
                    drawdown=snapshot.drawdown,
                    number_of_positions=snapshot.number_of_positions,
                )
                for snapshot in result.snapshots
            ]
        )
        result_store.save_equity_curve(
            [
                EquityCurveRecord(
                    experiment_id=experiment_id,
                    date=point.date,
                    portfolio_value=point.portfolio_value,
                    daily_return=point.daily_return,
                    cumulative_return=point.cumulative_return,
                )
                for point in result.equity_curve
            ]
        )
        result_store.save_backtest_summary(
            BacktestSummaryRecord(
                experiment_id=experiment_id,
                total_return=summary.total_return,
                annualized_return=summary.annualized_return,
                cagr=summary.cagr,
                volatility=summary.volatility,
                sharpe_ratio=summary.sharpe_ratio,
                sortino_ratio=summary.sortino_ratio,
                calmar_ratio=summary.calmar_ratio,
                max_drawdown=summary.max_drawdown,
                win_rate=summary.win_rate,
                profit_factor=summary.profit_factor,
                average_trade=summary.average_trade,
                number_of_trades=summary.number_of_trades,
                turnover=summary.turnover,
            )
        )
