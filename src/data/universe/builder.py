"""Default universe builder implementation."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from config.models import UniverseSettings
from core.types import DataVersion, SecurityId, Ticker, UniverseVersion
from data.protocols import DataAccess
from data.universe.filters import (
    is_delisted_on_or_before,
    passes_exchange_filter,
    passes_market_cap_filter,
    passes_price_filter,
    passes_security_type_filter,
)
from data.universe.liquidity import compute_addv, count_trading_days_before
from data.universe.versioning import hash_universe_settings
from schemas.data import DelistingInfo, PriceBar, SecurityMetadata
from schemas.universe import UniverseMembership, UniverseMembershipSnapshot, UniverseMetadata


class DefaultUniverseBuilder:
    """Builds point-in-time universe membership from data access and settings."""

    def __init__(self, settings: UniverseSettings | None = None) -> None:
        self._settings = settings or UniverseSettings()

    @property
    def settings(self) -> UniverseSettings:
        return self._settings

    def build_membership(
        self,
        evaluation_date: date,
        data_access: DataAccess,
    ) -> UniverseMembershipSnapshot:
        settings = self._settings
        memberships: list[UniverseMembership] = []

        store = data_access
        security_ids = list(store.list_security_ids())

        for security_id in security_ids:
            membership = self._evaluate_security(
                security_id=security_id,
                evaluation_date=evaluation_date,
                data_access=data_access,
                settings=settings,
            )
            memberships.append(membership)

        config_hash = hash_universe_settings(settings)
        metadata = UniverseMetadata(
            universe_version=UniverseVersion(f"universe_{config_hash}"),
            creation_timestamp=datetime.now(tz=UTC),
            configuration_hash=config_hash,
            data_version=DataVersion(str(data_access.data_version)),
        )
        return UniverseMembershipSnapshot(
            evaluation_date=evaluation_date,
            memberships=memberships,
            metadata=metadata,
        )

    def _evaluate_security(
        self,
        security_id: SecurityId,
        evaluation_date: date,
        data_access: DataAccess,
        settings: UniverseSettings,
    ) -> UniverseMembership:
        metadata = data_access.get_metadata(security_id, evaluation_date)
        delisting = data_access.get_delisting_info(security_id)
        bars = list(
            data_access.get_prices(
                security_id,
                start_date=evaluation_date - timedelta(days=800),
                end_date=evaluation_date,
                as_of_date=evaluation_date,
            )
        )

        ticker = metadata.ticker if metadata else Ticker(str(security_id))
        exchange = metadata.exchange if metadata else None
        sector = metadata.sector if metadata else None
        industry = metadata.industry if metadata else None

        is_member, reason, addv, market_cap = self._apply_filters(
            security_id=security_id,
            evaluation_date=evaluation_date,
            metadata=metadata,
            delisting=delisting,
            bars=bars,
            settings=settings,
        )

        return UniverseMembership(
            evaluation_date=evaluation_date,
            security_id=security_id,
            ticker=ticker,
            is_member=is_member,
            membership_reason=reason,
            exchange=exchange,
            sector=sector,
            industry=industry,
            market_cap=market_cap,
            average_daily_dollar_volume=addv,
        )

    def _apply_filters(
        self,
        security_id: SecurityId,
        evaluation_date: date,
        metadata: SecurityMetadata | None,
        delisting: DelistingInfo | None,
        bars: list[PriceBar],
        settings: UniverseSettings,
    ) -> tuple[bool, str | None, Decimal | None, Decimal | None]:
        if metadata is None:
            return False, "missing_metadata", None, None

        if is_delisted_on_or_before(delisting, evaluation_date):
            return False, "delisted", None, None

        if not passes_security_type_filter(settings):
            return False, "security_type_excluded", None, None

        if not passes_exchange_filter(metadata, settings):
            return False, "exchange_excluded", None, None

        if not bars:
            return False, "missing_price_history", None, None

        history_days = count_trading_days_before(bars, evaluation_date)
        if history_days < settings.minimum_trading_history_days:
            return False, "insufficient_trading_history", None, None

        if not passes_price_filter(bars, evaluation_date, settings.min_price):
            return False, "below_min_price", None, None

        addv = compute_addv(bars, evaluation_date)
        if addv is None or addv < Decimal(str(settings.min_average_daily_dollar_volume)):
            return False, "below_min_addv", addv, None

        market_cap: Decimal | None = None
        if settings.min_market_cap is not None:
            if not passes_market_cap_filter(market_cap, settings.min_market_cap):
                return False, "below_min_market_cap", addv, market_cap

        return True, "eligible", addv, market_cap
