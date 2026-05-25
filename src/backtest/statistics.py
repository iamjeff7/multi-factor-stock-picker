"""Backtest performance statistics."""

from __future__ import annotations

import math
from decimal import Decimal

from schemas.backtest import BacktestSummary, EquityCurvePoint, Trade


class DefaultPerformanceCalculator:
    """Computes summary statistics from trades and the equity curve."""

    TRADING_DAYS_PER_YEAR = 252

    def summarize(
        self,
        trades: list[Trade],
        equity_curve: list[EquityCurvePoint],
        initial_capital: Decimal,
    ) -> BacktestSummary:
        closed_trades = [trade for trade in trades if trade.exit_date is not None]
        total_return = self._total_return(equity_curve, initial_capital)
        daily_returns = self._daily_returns(equity_curve)
        volatility = self._volatility(daily_returns)
        max_drawdown = self._max_drawdown(equity_curve)
        annualized_return = self._annualized_return(total_return, equity_curve)
        cagr = annualized_return
        sharpe = self._sharpe_ratio(daily_returns)
        sortino = self._sortino_ratio(daily_returns)
        calmar = self._calmar_ratio(cagr, max_drawdown)
        win_rate, profit_factor, average_trade = self._trade_stats(closed_trades)
        turnover = self._turnover(closed_trades, equity_curve, initial_capital)

        return BacktestSummary(
            total_return=total_return,
            annualized_return=annualized_return,
            cagr=cagr,
            volatility=volatility,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            average_trade=average_trade,
            number_of_trades=len(closed_trades),
            turnover=turnover,
        )

    def _total_return(
        self,
        equity_curve: list[EquityCurvePoint],
        initial_capital: Decimal,
    ) -> Decimal:
        if not equity_curve or initial_capital <= Decimal("0"):
            return Decimal("0")
        final_value = equity_curve[-1].portfolio_value
        return (final_value / initial_capital) - Decimal("1")

    def _daily_returns(self, equity_curve: list[EquityCurvePoint]) -> list[float]:
        returns: list[float] = []
        for index in range(1, len(equity_curve)):
            previous = equity_curve[index - 1].portfolio_value
            current = equity_curve[index].portfolio_value
            if previous <= Decimal("0"):
                returns.append(0.0)
            else:
                returns.append(float((current / previous) - Decimal("1")))
        return returns

    def _volatility(self, daily_returns: list[float]) -> Decimal | None:
        if len(daily_returns) < 2:
            return None
        mean = sum(daily_returns) / len(daily_returns)
        variance = sum((value - mean) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
        return Decimal(str(math.sqrt(variance) * math.sqrt(self.TRADING_DAYS_PER_YEAR)))

    def _sharpe_ratio(self, daily_returns: list[float]) -> Decimal | None:
        if len(daily_returns) < 2:
            return None
        mean = sum(daily_returns) / len(daily_returns)
        variance = sum((value - mean) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
        std_dev = math.sqrt(variance)
        if std_dev == 0:
            return None
        annualized_mean = mean * self.TRADING_DAYS_PER_YEAR
        annualized_std = std_dev * math.sqrt(self.TRADING_DAYS_PER_YEAR)
        return Decimal(str(annualized_mean / annualized_std))

    def _sortino_ratio(self, daily_returns: list[float]) -> Decimal | None:
        if not daily_returns:
            return None
        mean = sum(daily_returns) / len(daily_returns)
        downside = [min(value, 0.0) for value in daily_returns]
        downside_variance = sum(value**2 for value in downside) / len(daily_returns)
        if downside_variance == 0:
            return None
        downside_dev = math.sqrt(downside_variance) * math.sqrt(self.TRADING_DAYS_PER_YEAR)
        annualized_mean = mean * self.TRADING_DAYS_PER_YEAR
        return Decimal(str(annualized_mean / downside_dev))

    def _max_drawdown(self, equity_curve: list[EquityCurvePoint]) -> Decimal | None:
        if not equity_curve:
            return None
        peak = equity_curve[0].portfolio_value
        max_drawdown = Decimal("0")
        for point in equity_curve:
            peak = max(peak, point.portfolio_value)
            if peak > Decimal("0"):
                drawdown = (point.portfolio_value / peak) - Decimal("1")
                max_drawdown = min(max_drawdown, drawdown)
        return max_drawdown

    def _annualized_return(
        self,
        total_return: Decimal,
        equity_curve: list[EquityCurvePoint],
    ) -> Decimal | None:
        if len(equity_curve) < 2:
            return None
        start = equity_curve[0].date
        end = equity_curve[-1].date
        years = (end - start).days / 365.25
        if years <= 0:
            return None
        growth = float(Decimal("1") + total_return)
        if growth <= 0:
            return None
        return Decimal(str(growth ** (1 / years) - 1))

    def _calmar_ratio(
        self,
        cagr: Decimal | None,
        max_drawdown: Decimal | None,
    ) -> Decimal | None:
        if cagr is None or max_drawdown is None or max_drawdown == Decimal("0"):
            return None
        return cagr / abs(max_drawdown)

    def _trade_stats(
        self,
        closed_trades: list[Trade],
    ) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
        if not closed_trades:
            return None, None, None

        winners = [trade for trade in closed_trades if (trade.net_pnl or Decimal("0")) > 0]
        win_rate = Decimal(str(len(winners) / len(closed_trades)))

        gross_wins: Decimal = sum(
            ((trade.net_pnl or Decimal("0")) for trade in winners),
            Decimal("0"),
        )
        losers = [trade for trade in closed_trades if (trade.net_pnl or Decimal("0")) < 0]
        gross_losses: Decimal = abs(
            sum(((trade.net_pnl or Decimal("0")) for trade in losers), Decimal("0"))
        )
        profit_factor = None if gross_losses == 0 else gross_wins / gross_losses

        average_trade = sum((trade.net_pnl or Decimal("0")) for trade in closed_trades) / Decimal(
            str(len(closed_trades))
        )
        return win_rate, profit_factor, average_trade

    def _turnover(
        self,
        closed_trades: list[Trade],
        equity_curve: list[EquityCurvePoint],
        initial_capital: Decimal,
    ) -> Decimal | None:
        if not closed_trades:
            return Decimal("0")
        traded_notional = sum(
            (trade.entry_price * trade.shares) + ((trade.exit_price or Decimal("0")) * trade.shares)
            for trade in closed_trades
        )
        avg_value = (
            sum(point.portfolio_value for point in equity_curve) / Decimal(str(len(equity_curve)))
            if equity_curve
            else initial_capital
        )
        if avg_value <= Decimal("0"):
            return None
        return traded_notional / avg_value
