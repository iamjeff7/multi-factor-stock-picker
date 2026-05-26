"""Resolve securities for unified experiment configs."""

from __future__ import annotations

from datetime import date

from backtest.experiment_config import ExperimentSecurity
from backtest.universe_resolution import demo_universe_settings
from config.models import UniverseSettings
from data.protocols import DataAccess
from data.universe.builder import DefaultUniverseBuilder
from experiments.config import UnifiedExperimentConfig


def resolve_unified_config(
    config: UnifiedExperimentConfig,
    data_access: DataAccess,
    *,
    evaluation_date: date | None = None,
) -> UnifiedExperimentConfig:
    if config.universe is None and config.securities:
        return config
    as_of = evaluation_date or config.start_date
    if as_of is None:
        raise ValueError("start_date is required to resolve universe membership")
    if config.universe is None:
        return config

    builder = DefaultUniverseBuilder(config.universe)
    snapshot = builder.build_membership(as_of, data_access)
    members = [row for row in snapshot.memberships if row.is_member]
    securities = [
        ExperimentSecurity(security_id=row.security_id, ticker=row.ticker) for row in members
    ]
    return config.model_copy(update={"securities": securities})


def mag7_securities() -> list[ExperimentSecurity]:
    from core.types import SecurityId, Ticker

    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
    return [
        ExperimentSecurity(security_id=SecurityId(f"SEC_{ticker}"), ticker=Ticker(ticker))
        for ticker in tickers
    ]


def default_mag7_universe() -> UniverseSettings:
    return demo_universe_settings()
