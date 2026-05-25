"""Example entry signal stub for interface demonstration."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.types import SignalId
from data.protocols import DataAccess
from entry_signals.base import BaseEntrySignal
from entry_signals.enums import MissingDataPolicy, SignalCategory
from schemas.entry import SignalMetadata
from schemas.universe import UniverseMembership


class ExampleStubEntrySignal(BaseEntrySignal):
    """Deterministic stub that hashes security_id into a raw signal value."""

    def __init__(
        self,
        *,
        missing_data_policy: MissingDataPolicy = MissingDataPolicy.ASSIGN_NULL,
        default_value: Decimal | None = None,
        return_none_for_security_suffix: str | None = None,
    ) -> None:
        metadata = SignalMetadata(
            signal_id=SignalId("example_stub"),
            signal_name="Example Stub Entry Signal",
            signal_description="Demonstrates BaseEntrySignal without real market logic",
            signal_category=SignalCategory.MOMENTUM,
            signal_version="1.0",
            missing_data_policy=missing_data_policy,
            higher_is_better=True,
        )
        super().__init__(metadata, default_value=default_value)
        self._return_none_for_security_suffix = return_none_for_security_suffix

    def _compute_raw_value(
        self,
        evaluation_date: date,
        membership: UniverseMembership,
        data_access: DataAccess,
    ) -> Decimal | None:
        del evaluation_date, data_access

        security_id = str(membership.security_id)
        if (
            self._return_none_for_security_suffix is not None
            and security_id.endswith(self._return_none_for_security_suffix)
        ):
            return None

        return Decimal(str(abs(hash(security_id)) % 1000)) / Decimal("100")
