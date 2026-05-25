"""Entry signal base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from core.exceptions import ValidationError
from core.types import SignalId
from data.protocols import DataAccess
from entry_signals.enums import MissingDataPolicy
from entry_signals.validator import EntrySignalValidator, is_finite_decimal
from schemas.entry import EntrySignalResult, SignalMetadata
from schemas.universe import UniverseMembership, UniverseMembershipSnapshot


class BaseEntrySignal(ABC):
    """Template-method base for entry signal implementations."""

    def __init__(
        self,
        metadata: SignalMetadata,
        *,
        default_value: Decimal | None = None,
        validator: EntrySignalValidator | None = None,
    ) -> None:
        self._metadata = metadata
        self._default_value = default_value
        self._validator = validator or EntrySignalValidator()

    @property
    def signal_id(self) -> str:
        return str(self._metadata.signal_id)

    @property
    def metadata(self) -> SignalMetadata:
        return self._metadata

    @property
    def missing_data_policy(self) -> MissingDataPolicy:
        return self._metadata.missing_data_policy

    def calculate(
        self,
        evaluation_date: date,
        universe: UniverseMembershipSnapshot,
        data_access: DataAccess,
    ) -> Sequence[EntrySignalResult]:
        self._validator.validate_inputs_or_raise(
            evaluation_date=evaluation_date,
            universe=universe,
            metadata=self._metadata,
        )

        results: list[EntrySignalResult] = []
        for membership in universe.memberships:
            if not membership.is_member:
                continue

            raw_value = self._compute_raw_value(
                evaluation_date=evaluation_date,
                membership=membership,
                data_access=data_access,
            )
            result = self._apply_missing_data_policy(
                evaluation_date=evaluation_date,
                membership=membership,
                raw_value=raw_value,
            )
            if result is not None:
                results.append(result)

        self._validator.validate_results_or_raise(results)
        return results

    @abstractmethod
    def _compute_raw_value(
        self,
        evaluation_date: date,
        membership: UniverseMembership,
        data_access: DataAccess,
    ) -> Decimal | None:
        """Compute the raw signal value for one eligible security."""

    def _apply_missing_data_policy(
        self,
        evaluation_date: date,
        membership: UniverseMembership,
        raw_value: Decimal | None,
    ) -> EntrySignalResult | None:
        if raw_value is not None:
            return self._build_result(
                evaluation_date=evaluation_date,
                membership=membership,
                raw_signal_value=raw_value,
            )

        policy = self.missing_data_policy
        if policy is MissingDataPolicy.EXCLUDE_SECURITY:
            return None
        if policy is MissingDataPolicy.ASSIGN_NULL:
            return self._build_result(
                evaluation_date=evaluation_date,
                membership=membership,
                raw_signal_value=None,
            )
        if policy is MissingDataPolicy.ASSIGN_DEFAULT_VALUE:
            if self._default_value is None:
                raise ValidationError(
                    f"Signal {self.signal_id} requires default_value for "
                    "assign_default_value missing-data policy"
                )
            return self._build_result(
                evaluation_date=evaluation_date,
                membership=membership,
                raw_signal_value=self._default_value,
            )

        raise ValidationError(f"Unsupported missing-data policy: {policy}")

    def _build_result(
        self,
        evaluation_date: date,
        membership: UniverseMembership,
        raw_signal_value: Decimal | None,
    ) -> EntrySignalResult:
        if raw_signal_value is not None and not is_finite_decimal(raw_signal_value):
            raise ValidationError(
                f"Non-finite raw_signal_value for security {membership.security_id}"
            )
        return EntrySignalResult(
            evaluation_date=evaluation_date,
            security_id=membership.security_id,
            ticker=membership.ticker,
            signal_id=SignalId(self.signal_id),
            signal_version=self._metadata.signal_version,
            raw_signal_value=raw_signal_value,
        )
