"""Entry signal base class tests."""

from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from core.types import SignalId
from data.protocols import DataAccess
from entry_signals.base import BaseEntrySignal
from entry_signals.enums import MissingDataPolicy, SignalCategory
from entry_signals.validator import EntrySignalValidator
from schemas.entry import SignalMetadata
from schemas.universe import UniverseMembership, UniverseMembershipSnapshot


class _RecordingEntrySignal(BaseEntrySignal):
    def __init__(
        self,
        metadata: SignalMetadata,
        values: dict[str, Decimal | None],
        *,
        default_value: Decimal | None = None,
    ) -> None:
        super().__init__(metadata, default_value=default_value)
        self._values = values

    def _compute_raw_value(
        self,
        evaluation_date: date,
        membership: UniverseMembership,
        data_access: DataAccess,
    ) -> Decimal | None:
        del evaluation_date, data_access
        return self._values.get(str(membership.security_id))


def _metadata(policy: MissingDataPolicy) -> SignalMetadata:
    return SignalMetadata(
        signal_id=SignalId("test_signal"),
        signal_name="Test Signal",
        signal_category=SignalCategory.VALUE,
        signal_version="1.0",
        missing_data_policy=policy,
        lower_is_better=True,
    )


def test_base_entry_signal_excludes_missing_securities(
    sample_universe_snapshot: UniverseMembershipSnapshot,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingEntrySignal(
        _metadata(MissingDataPolicy.EXCLUDE_SECURITY),
        {"100": Decimal("1.5"), "200": None},
    )
    results = signal.calculate(date(2020, 1, 31), sample_universe_snapshot, mock_data_access)
    assert len(results) == 1
    assert results[0].security_id == sample_universe_snapshot.memberships[0].security_id


def test_base_entry_signal_assigns_null(
    sample_universe_snapshot: UniverseMembershipSnapshot,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingEntrySignal(
        _metadata(MissingDataPolicy.ASSIGN_NULL),
        {"100": Decimal("1.5"), "200": None},
    )
    results = signal.calculate(date(2020, 1, 31), sample_universe_snapshot, mock_data_access)
    assert len(results) == 2
    assert results[1].raw_signal_value is None


def test_base_entry_signal_assigns_default_value(
    sample_universe_snapshot: UniverseMembershipSnapshot,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingEntrySignal(
        _metadata(MissingDataPolicy.ASSIGN_DEFAULT_VALUE),
        {"100": Decimal("1.5"), "200": None},
        default_value=Decimal("0"),
    )
    results = signal.calculate(date(2020, 1, 31), sample_universe_snapshot, mock_data_access)
    assert results[1].raw_signal_value == Decimal("0")


def test_base_entry_signal_requires_default_for_default_policy(
    sample_universe_snapshot: UniverseMembershipSnapshot,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingEntrySignal(
        _metadata(MissingDataPolicy.ASSIGN_DEFAULT_VALUE),
        {"100": None},
    )
    with pytest.raises(ValidationError, match="default_value"):
        signal.calculate(date(2020, 1, 31), sample_universe_snapshot, mock_data_access)


def test_base_entry_signal_validates_outputs(
    sample_universe_snapshot: UniverseMembershipSnapshot,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingEntrySignal(
        _metadata(MissingDataPolicy.ASSIGN_NULL),
        {"100": Decimal("NaN"), "200": Decimal("1")},
    )
    with pytest.raises(ValidationError, match="Non-finite"):
        signal.calculate(date(2020, 1, 31), sample_universe_snapshot, mock_data_access)


def test_base_entry_signal_validates_inputs(
    sample_universe_snapshot: UniverseMembershipSnapshot,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingEntrySignal(
        _metadata(MissingDataPolicy.ASSIGN_NULL),
        {"100": Decimal("1")},
    )
    with pytest.raises(ValidationError, match="evaluation date"):
        signal.calculate(date(2020, 2, 1), sample_universe_snapshot, mock_data_access)


def test_entry_signal_validator_detects_duplicates() -> None:
    from core.types import SecurityId, Ticker
    from schemas.entry import EntrySignalResult

    validator = EntrySignalValidator()
    rows = [
        EntrySignalResult(
            evaluation_date=date(2020, 1, 31),
            security_id=SecurityId("100"),
            ticker=Ticker("AAA"),
            signal_id=SignalId("test"),
            signal_version="1.0",
            raw_signal_value=Decimal("1"),
        ),
        EntrySignalResult(
            evaluation_date=date(2020, 1, 31),
            security_id=SecurityId("100"),
            ticker=Ticker("AAA"),
            signal_id=SignalId("test"),
            signal_version="1.0",
            raw_signal_value=Decimal("2"),
        ),
    ]
    report = validator.validate_results(rows)
    assert report.passed is False
