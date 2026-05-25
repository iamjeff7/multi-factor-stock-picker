"""Optional winsorization preprocessing tests."""

from decimal import Decimal

from core.types import SecurityId
from factors.scoring.config import WinsorizeConfig
from factors.scoring.preprocessing import winsorize_observations
from factors.scoring.ranking import RankObservation


def test_winsorize_clips_extreme_values() -> None:
    observations = [
        RankObservation(SecurityId(f"{index}"), Decimal(index))
        for index in range(10)
    ]
    clipped = winsorize_observations(
        observations,
        WinsorizeConfig(lower_pct=Decimal("0.1"), upper_pct=Decimal("0.9")),
    )
    by_id = {row.security_id: row.raw_value for row in clipped}

    assert by_id[SecurityId("0")] == Decimal("0.9")
    assert by_id[SecurityId("9")] == Decimal("8.1")
    assert by_id[SecurityId("5")] == Decimal("5")
