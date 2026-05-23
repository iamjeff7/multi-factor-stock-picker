"""Point-in-time corporate action filtering."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from schemas.data import CorporateAction


def filter_actions_as_of(
    actions: Sequence[CorporateAction],
    as_of_date: date,
) -> list[CorporateAction]:
    return [action for action in actions if action.action_date <= as_of_date]
