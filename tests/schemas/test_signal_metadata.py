"""Schema contract tests."""

from core.types import SignalId
from entry_signals.enums import SignalCategory
from schemas.entry import SignalMetadata


def test_signal_metadata_requires_direction() -> None:
    meta = SignalMetadata(
        signal_id=SignalId("momentum_12m"),
        signal_name="12 Month Momentum",
        signal_category=SignalCategory.MOMENTUM,
        signal_version="1.0",
        higher_is_better=True,
    )
    assert meta.direction.value == "higher_is_better"
