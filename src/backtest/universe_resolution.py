"""Resolve experiment universes from explicit lists or the universe builder."""

from __future__ import annotations

from datetime import date

from backtest.experiment_config import ExperimentSecurity, SingleFactorExperimentConfig
from config.models import UniverseSettings
from core.exceptions import ValidationError
from data.protocols import DataAccess
from data.universe.builder import DefaultUniverseBuilder
from data.universe.protocols import UniverseBuilder


def resolve_experiment_securities(
    config: SingleFactorExperimentConfig,
    data_access: DataAccess,
    *,
    evaluation_date: date | None = None,
    universe_builder: UniverseBuilder | None = None,
) -> list[ExperimentSecurity]:
    """Return explicit securities or builder-selected members for the evaluation date."""
    if config.universe is None:
        return list(config.securities)

    as_of_date = evaluation_date or config.start_date
    builder = universe_builder or DefaultUniverseBuilder(config.universe)
    snapshot = builder.build_membership(as_of_date, data_access)
    members = [membership for membership in snapshot.memberships if membership.is_member]
    if not members:
        raise ValidationError(
            f"No eligible universe members on {as_of_date} with configured filters"
        )

    return [
        ExperimentSecurity(security_id=membership.security_id, ticker=membership.ticker)
        for membership in members
    ]


def with_resolved_securities(
    config: SingleFactorExperimentConfig,
    data_access: DataAccess,
    *,
    evaluation_date: date | None = None,
    universe_builder: UniverseBuilder | None = None,
) -> SingleFactorExperimentConfig:
    """Return a config copy with universe-resolved securities and validated top_n."""
    securities = resolve_experiment_securities(
        config,
        data_access,
        evaluation_date=evaluation_date,
        universe_builder=universe_builder,
    )
    if config.top_n is not None and config.top_n > len(securities):
        raise ValidationError("top_n cannot exceed the number of resolved securities")

    return config.model_copy(update={"securities": securities})


def demo_universe_settings() -> UniverseSettings:
    """Universe filters suitable for the Mag7 demo fixture."""
    return UniverseSettings(
        min_price=5.0,
        min_average_daily_dollar_volume=1_000_000,
        minimum_trading_history_days=252,
    )
