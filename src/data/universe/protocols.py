"""Universe construction interfaces."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from data.protocols import DataAccess
from schemas.data import ValidationReport
from schemas.universe import UniverseMembershipSnapshot


class UniverseBuilder(Protocol):
    """Builds point-in-time universe membership for an evaluation date."""

    def build_membership(
        self,
        evaluation_date: date,
        data_access: DataAccess,
    ) -> UniverseMembershipSnapshot: ...


class UniverseValidator(Protocol):
    """Validates universe membership snapshots."""

    def validate(self, snapshot: UniverseMembershipSnapshot) -> ValidationReport: ...
