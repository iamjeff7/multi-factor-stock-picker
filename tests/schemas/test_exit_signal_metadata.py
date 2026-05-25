"""Exit signal metadata schema tests."""


from core.types import SignalId
from exit_signals.enums import ExitCategory, MissingDataPolicy
from schemas.enums import EvaluationFrequency
from schemas.exit import ExitSignalMetadata


def test_exit_signal_metadata_defaults_to_daily() -> None:
    metadata = ExitSignalMetadata(
        signal_id=SignalId("stop_loss_10pct"),
        signal_name="10 Percent Stop Loss",
        signal_category=ExitCategory.STOP_LOSS,
        signal_version="1.0",
        missing_data_policy=MissingDataPolicy.HOLD_POSITION,
    )
    assert metadata.evaluation_frequency is EvaluationFrequency.DAILY
