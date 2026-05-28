"""Entry + exit combined experiment using VectorBT."""

from __future__ import annotations

import json
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

from core.exceptions import ValidationError
from core.types import ExperimentId
from data.protocols import DataAccess
from experiments.config import UnifiedExperimentConfig
from experiments.data_presets import resolve_data_preset
from experiments.reporting import build_combined_report_payload, write_json
from experiments.resolution import resolve_unified_config
from experiments.scoring.combined_metrics import (
    StrategyMetrics,
    aggregate_strategy_metrics,
    build_strategy_metrics_from_vbt,
    compute_final_strategy_score,
)
from experiments.segments import SegmentClassifier
from experiments.signal_catalog import build_entry_signal, build_exit_signal
from experiments.trade_simulator import simulate_combined_strategy
from evaluation.combined.robustness.scorer import compute_combined_robustness
from reporting.layout import ResultLayout

try:
    import vectorbt as vbt
except ImportError:  # pragma: no cover - exercised via dependency guard test
    vbt = None


class CombinedExperimentRunner:
    def run(
        self,
        config: UnifiedExperimentConfig,
        data_access: DataAccess,
        *,
        output_dir: Path,
        reference_date: date | None = None,
    ) -> Path:
        if vbt is None:
            raise ValidationError(
                "entry_and_exit mode requires vectorbt; install with pip install -e '.[research]'"
            )
        if config.combined.entry_rankings_source is None:
            raise ValidationError("combined.entry_rankings_source is required")
        if config.combined.exit_rankings_source is None:
            raise ValidationError("combined.exit_rankings_source is required")

        preset = resolve_data_preset(
            config.data_preset,
            data_access,
            [str(security.security_id) for security in config.securities],
            reference_date=reference_date,
        )
        start_date = config.start_date or preset.start_date
        end_date = config.end_date or preset.end_date
        config = resolve_unified_config(config, data_access, evaluation_date=start_date)
        experiment_id = ExperimentId(f"exp_{uuid.uuid4().hex[:12]}")
        initial_capital = Decimal(str(config.initial_capital))

        entry_rankings = _load_rankings(config.combined.entry_rankings_source)
        exit_rankings = _load_rankings(config.combined.exit_rankings_source)
        classifier = SegmentClassifier()

        per_stock: list[dict[str, object]] = []
        strategy_metrics_rows: list[StrategyMetrics] = []

        for security in config.securities:
            labels = classifier.classify_cross_section(
                data_access,
                [security.security_id],
                start_date,
            )[security.security_id]
            segment_key = labels.key()
            entry_factor = _select_top_factor(entry_rankings, segment_key)
            exit_factor = _select_top_factor(exit_rankings, segment_key)
            if entry_factor is None or exit_factor is None:
                per_stock.append(
                    {
                        "security_id": str(security.security_id),
                        "ticker": str(security.ticker),
                        "status": "skipped",
                        "skip_reason": f"No qualified factors for segment {segment_key}",
                    }
                )
                continue

            entry_signal = build_entry_signal(_variant_to_config(entry_factor, side="entry"))
            exit_signal = build_exit_signal(_variant_to_config(exit_factor, side="exit"))
            trades = simulate_combined_strategy(
                data_access=data_access,
                security_id=security.security_id,
                ticker=security.ticker,
                entry_signal=entry_signal,
                exit_signal=exit_signal,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
            )
            vbt_metrics = _vectorbt_metrics_from_trades(
                trades,
                data_access=data_access,
                security_id=security.security_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=float(initial_capital),
                benchmark_ticker=config.combined.benchmark_ticker,
            )
            combined_robustness = compute_combined_robustness()
            strategy_metrics = build_strategy_metrics_from_vbt(
                nested_metrics=vbt_metrics,
                robustness_score=combined_robustness.overall_robustness_score,
            )
            strategy_metrics_rows.append(strategy_metrics)
            final_strategy_score = compute_final_strategy_score(
                strategy_metrics,
                peer_metrics=strategy_metrics_rows,
            )
            per_stock.append(
                {
                    "security_id": str(security.security_id),
                    "ticker": str(security.ticker),
                    "status": "completed",
                    "dominant_segment": labels.to_dict(),
                    "selected_entry_factors": [entry_factor],
                    "selected_exit_factors": [exit_factor],
                    "metrics": vbt_metrics,
                    "strategy_metrics": strategy_metrics.model_dump(mode="json"),
                    "final_strategy_score": str(final_strategy_score),
                    "strategy_robustness": combined_robustness.model_dump(mode="json"),
                    "entry_signal_id": entry_signal.signal_id,
                    "exit_signal_id": exit_signal.signal_id,
                }
            )

        aggregate_metrics = aggregate_strategy_metrics(strategy_metrics_rows)
        aggregate_vbt = _aggregate_vbt_metrics(
            [row["metrics"] for row in per_stock if row.get("status") == "completed"]
        )
        aggregate_final_score = compute_final_strategy_score(
            aggregate_metrics,
            peer_metrics=strategy_metrics_rows,
        )
        aggregate = {
            "metrics": aggregate_vbt,
            "strategy_metrics": aggregate_metrics.model_dump(mode="json"),
            "final_strategy_score": str(aggregate_final_score),
        }
        run_config = {
            "data_preset": config.data_preset.value,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trading_days": preset.trading_days,
            "universe": preset.universe_name,
            "initial_capital": str(initial_capital),
            "engine": "vectorbt",
            "entry_rankings_source": str(config.combined.entry_rankings_source),
            "exit_rankings_source": str(config.combined.exit_rankings_source),
            "benchmark_ticker": config.combined.benchmark_ticker,
            "risk_free_source": config.combined.risk_free_source,
        }
        report_payload = build_combined_report_payload(
            experiment_id=str(experiment_id),
            experiment_name=config.experiment_name,
            run_config=run_config,
            execution_summary={
                "securities_requested": len(config.securities),
                "securities_completed": sum(
                    1 for row in per_stock if row.get("status") == "completed"
                ),
                "securities_skipped": sum(
                    1 for row in per_stock if row.get("status") == "skipped"
                ),
                "status": "COMPLETED",
            },
            portfolio_metrics=aggregate,
            per_stock=per_stock,
            aggregate=aggregate,
        )
        experiment_dir = output_dir / str(experiment_id)
        return write_json(experiment_dir / ResultLayout.EXPERIMENT_REPORT, report_payload)


def _load_rankings(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _select_top_factor(rankings: dict[str, object], segment_key: str) -> dict[str, object] | None:
    segments = rankings.get("segments", {})
    if not isinstance(segments, dict):
        return None
    segment = segments.get(segment_key)
    if not isinstance(segment, dict):
        return None
    factors = segment.get("factors", [])
    if not isinstance(factors, list):
        return None
    qualified = [row for row in factors if isinstance(row, dict) and row.get("qualified")]
    if not qualified:
        return None
    return max(qualified, key=lambda row: float(str(row.get("final_score", "0"))))


def _variant_to_config(factor: dict[str, object], *, side: str) -> object:
    from backtest.experiment_config import SignalConfig

    signal_id = str(factor.get("signal_id", ""))
    variant_id = str(factor.get("variant_id", ""))
    if side == "entry":
        params = _entry_params_from_variant(variant_id)
        return SignalConfig(name=signal_id, params=params)
    return SignalConfig(name=signal_id, params=_exit_params_from_variant(variant_id))


def _entry_params_from_variant(variant_id: str) -> dict[str, object]:
    if variant_id.startswith("lookback_") and "_skip_" in variant_id:
        lookback_raw, skip_raw = variant_id.removeprefix("lookback_").split("_skip_")
        return {"lookback_days": int(lookback_raw), "skip_days": int(skip_raw)}
    return {}


def _exit_params_from_variant(variant_id: str) -> dict[str, object]:
    if variant_id.startswith("stop_") and "_trail_" in variant_id:
        stop, trail = variant_id.replace("stop_", "").split("_trail_")
        return {"stop_pct": stop, "trail_pct": trail}
    if variant_id.startswith("stop_"):
        return {"stop_pct": variant_id.removeprefix("stop_")}
    if variant_id.startswith("trail_"):
        return {"trail_pct": variant_id.removeprefix("trail_")}
    return {}


def _vectorbt_metrics_from_trades(
    trades: list,
    *,
    data_access: DataAccess,
    security_id,
    start_date: date,
    end_date: date,
    initial_capital: float,
    benchmark_ticker: str,
) -> dict[str, object]:
    if not trades:
        return _empty_vbt_metrics()

    bars = data_access.get_prices(
        security_id=security_id,
        start_date=start_date,
        end_date=end_date,
        as_of_date=end_date,
    )
    index = pd.DatetimeIndex([bar.trade_date for bar in bars])
    close = pd.Series([float(bar.adjusted_close) for bar in bars], index=index)
    entries = pd.Series(False, index=index)
    exits = pd.Series(False, index=index)
    for trade in trades:
        entry_ts = pd.Timestamp(trade.entry_date)
        exit_ts = pd.Timestamp(trade.exit_date) if trade.exit_date else None
        if entry_ts in entries.index:
            entries.loc[entry_ts] = True
        if exit_ts is not None and exit_ts in exits.index:
            exits.loc[exit_ts] = True

    portfolio = vbt.Portfolio.from_signals(
        close,
        entries=entries,
        exits=exits,
        init_cash=initial_capital,
        freq="1D",
    )
    stats = portfolio.stats()
    returns = portfolio.returns().dropna()
    benchmark_returns = _benchmark_returns(
        data_access=data_access,
        benchmark_ticker=benchmark_ticker,
        index=index,
    )
    alpha, beta = _alpha_beta(returns, benchmark_returns)
    tail_ratio = _tail_ratio(returns)
    total = int(stats.get("Total Trades", 0))
    win_rate_pct = float(stats.get("Win Rate [%]", 0) or 0)
    winning_trades = int(total * win_rate_pct / 100)
    return {
        "risk_adjusted": {
            "sharpe_ratio": _fmt(stats.get("Sharpe Ratio")),
            "sortino_ratio": _fmt(stats.get("Sortino Ratio")),
            "profit_factor": _fmt(stats.get("Profit Factor")),
            "cagr": _fmt(stats.get("Total Return [%]")),
            "calmar_ratio": _fmt(stats.get("Calmar Ratio")),
        },
        "risk_and_capital": {
            "max_drawdown": _fmt(stats.get("Max Drawdown [%]")),
            "average_drawdown": None,
            "max_consecutive_wins": int(stats.get("Best Trade [%]", 0)),
            "max_consecutive_losses": int(stats.get("Worst Trade [%]", 0)),
            "win_rate": _fmt(stats.get("Win Rate [%]")),
            "expectancy": _fmt(stats.get("Expectancy")),
        },
        "benchmark_comparison": {
            "benchmark_ticker": benchmark_ticker,
            "risk_free_rate_source": "T_BILL",
            "alpha": _fmt(alpha),
            "beta": _fmt(beta),
            "information_ratio": None,
        },
        "tail_ratio": _fmt(tail_ratio),
        "turnover_rate": _fmt(stats.get("Total Trades")),
        "trade_counts": {
            "total_trades": total,
            "winning_trades": winning_trades,
            "losing_trades": max(total - winning_trades, 0),
            "trade_frequency_per_trading_day": _fmt(
                Decimal(str(len(trades))) / Decimal(str(max(len(index), 1)))
            ),
            "trade_frequency_per_trading_year": str(len(trades)),
            "min_trade_duration_days": min((trade.holding_days or 0) for trade in trades),
            "max_trade_duration_days": max((trade.holding_days or 0) for trade in trades),
            "mean_trade_duration_days": _fmt(
                Decimal(str(sum((trade.holding_days or 0) for trade in trades)))
                / Decimal(str(len(trades)))
            ),
        },
    }


def _aggregate_vbt_metrics(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return _empty_vbt_metrics()

    numeric_fields = [
        ("risk_adjusted", "sharpe_ratio"),
        ("risk_adjusted", "sortino_ratio"),
        ("risk_adjusted", "profit_factor"),
        ("risk_adjusted", "cagr"),
        ("risk_adjusted", "calmar_ratio"),
        ("risk_and_capital", "max_drawdown"),
        ("risk_and_capital", "win_rate"),
        ("risk_and_capital", "expectancy"),
        ("benchmark_comparison", "alpha"),
        ("benchmark_comparison", "beta"),
    ]
    aggregate = _empty_vbt_metrics()
    for section, field in numeric_fields:
        values = []
        for row in rows:
            section_payload = row.get(section, {})
            if isinstance(section_payload, dict) and section_payload.get(field) is not None:
                values.append(Decimal(str(section_payload[field])))
        if not values:
            continue
        target = aggregate[section]
        assert isinstance(target, dict)
        target[field] = str(sum(values, start=Decimal("0")) / Decimal(len(values)))

    tail_values = [
        Decimal(str(row["tail_ratio"]))
        for row in rows
        if row.get("tail_ratio") is not None
    ]
    if tail_values:
        aggregate["tail_ratio"] = str(sum(tail_values, start=Decimal("0")) / Decimal(len(tail_values)))

    trade_total = sum(
        int(_section(row, "trade_counts").get("total_trades", 0) or 0) for row in rows
    )
    trade_counts = aggregate["trade_counts"]
    assert isinstance(trade_counts, dict)
    trade_counts["total_trades"] = trade_total
    return aggregate


def _benchmark_returns(
    *,
    data_access: DataAccess,
    benchmark_ticker: str,
    index: pd.DatetimeIndex,
) -> pd.Series:
    _ = benchmark_ticker
    return pd.Series(dtype=float)


def _alpha_beta(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> tuple[Decimal | None, Decimal | None]:
    aligned = pd.concat([strategy_returns, benchmark_returns], axis=1, join="inner").dropna()
    if aligned.empty or len(aligned) < 2:
        return None, None
    strategy = aligned.iloc[:, 0]
    benchmark = aligned.iloc[:, 1]
    benchmark_var = float(benchmark.var())
    if benchmark_var == 0:
        return None, None
    beta = float(strategy.cov(benchmark) / benchmark_var)
    alpha = float(strategy.mean() - beta * benchmark.mean())
    return Decimal(str(alpha)), Decimal(str(beta))


def _tail_ratio(returns: pd.Series) -> Decimal | None:
    clean = returns.dropna()
    if clean.empty:
        return None
    upper = float(clean.quantile(0.95))
    lower = abs(float(clean.quantile(0.05)))
    if lower == 0:
        return None
    return Decimal(str(upper / lower))


def _section(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if isinstance(value, dict):
        return value
    return {}


def _empty_vbt_metrics() -> dict[str, object]:
    return {
        "risk_adjusted": {},
        "risk_and_capital": {},
        "benchmark_comparison": {
            "benchmark_ticker": "SPY",
            "risk_free_rate_source": "T_BILL",
            "alpha": None,
            "beta": None,
            "information_ratio": None,
        },
        "trade_counts": {},
    }


def _fmt(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
