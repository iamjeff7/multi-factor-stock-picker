"""Entry policy tests."""

from datetime import date
from decimal import Decimal

from backtest.entry_policy import SignalPresentEntryPolicy, ThresholdEntryPolicy, TopNEntryPolicy
from core.types import SecurityId, SignalId, Ticker
from entry_signals.enums import MissingDataPolicy, SignalCategory
from schemas.entry import EntrySignalResult, SignalMetadata


def _signal(value: Decimal | None) -> EntrySignalResult:
    return EntrySignalResult(
        evaluation_date=date(2020, 1, 2),
        security_id=SecurityId("SEC_TEST"),
        ticker=Ticker("TEST"),
        signal_id=SignalId("test"),
        signal_version="1.0",
        raw_signal_value=value,
    )


def test_signal_present_entry_policy() -> None:
    policy = SignalPresentEntryPolicy()
    assert policy.should_enter(_signal(Decimal("1"))) is True
    assert policy.should_enter(_signal(None)) is False
    assert policy.should_enter(None) is False


def test_threshold_entry_policy_higher_is_better() -> None:
    metadata = SignalMetadata(
        signal_id=SignalId("test"),
        signal_name="Test",
        signal_category=SignalCategory.MOMENTUM,
        signal_version="1.0",
        missing_data_policy=MissingDataPolicy.ASSIGN_NULL,
        higher_is_better=True,
    )
    policy = ThresholdEntryPolicy(metadata, Decimal("10"))
    assert policy.should_enter(_signal(Decimal("11"))) is True
    assert policy.should_enter(_signal(Decimal("9"))) is False


def test_top_n_entry_policy_requires_rank_membership() -> None:
    evaluation_date = date(2020, 1, 2)
    selected = {SecurityId("SEC_TEST")}
    policy = TopNEntryPolicy({evaluation_date: selected})

    assert policy.should_enter(_signal(Decimal("1"))) is True
    assert policy.should_enter(None) is False
    assert policy.should_enter(_signal(None)) is False

    other = EntrySignalResult(
        evaluation_date=evaluation_date,
        security_id=SecurityId("SEC_OTHER"),
        ticker=Ticker("OTHER"),
        signal_id=SignalId("test"),
        signal_version="1.0",
        raw_signal_value=Decimal("1"),
    )
    assert policy.should_enter(other) is False
