"""Research validation enforcement."""

from __future__ import annotations

from datetime import date

from core.enums import ResearchPhase, ResearchMode, SampleScope
from research.config import ResearchSettings
from research.sample_split import SampleSplit, last_completed_calendar_year_end


def validate_research_settings(
    settings: ResearchSettings,
    *,
    start_date: date,
    end_date: date,
    split: SampleSplit | None = None,
) -> None:
    """Enforce discovery/OOS access rules and calendar bounds."""
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    calendar_end = _calendar_end(settings, end_date)

    if start_date < settings.calendar_start:
        raise ValueError(
            f"start_date {start_date} is before research calendar_start "
            f"{settings.calendar_start}"
        )
    if settings.research_mode is ResearchMode.PRODUCTION and end_date > calendar_end:
        raise ValueError(
            f"end_date {end_date} exceeds allowed research calendar end {calendar_end}"
        )

    if settings.research_phase is ResearchPhase.DISCOVERY:
        if settings.sample_scope is not SampleScope.IN_SAMPLE:
            raise ValueError(
                "DISCOVERY phase requires sample_scope=IS; "
                "OOS and FULL scopes are forbidden during discovery"
            )
        if split is not None and end_date >= split.split_date:
            raise ValueError(
                f"DISCOVERY runs must end before OOS split_date {split.split_date}; "
                f"got end_date={end_date}"
            )

    if settings.research_phase is ResearchPhase.VALIDATION and split is not None:
        if settings.sample_scope is SampleScope.OUT_OF_SAMPLE:
            if start_date < split.split_date:
                raise ValueError(
                    f"OOS validation runs must start on or after split_date "
                    f"{split.split_date}; got start_date={start_date}"
                )
        if settings.sample_scope is SampleScope.IN_SAMPLE and end_date >= split.split_date:
            raise ValueError(
                f"IS validation runs must end before split_date {split.split_date}; "
                f"got end_date={end_date}"
            )


def _calendar_end(settings: ResearchSettings, configured_end: date) -> date:
    if settings.research_mode is ResearchMode.PRODUCTION:
        return last_completed_calendar_year_end()
    return configured_end
