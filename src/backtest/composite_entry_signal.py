"""Entry signal backed by precomputed composite scores."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from core.types import SecurityId, SignalId
from data.protocols import DataAccess
from entry_signals.enums import MissingDataPolicy, SignalCategory
from schemas.entry import EntrySignalResult, SignalMetadata
from schemas.factors import CompositeScore
from schemas.universe import UniverseMembershipSnapshot


class CompositeScoreEntrySignal:
    """Expose composite ranks as entry signal values for per-stock backtests."""

    def __init__(
        self,
        composite_scores: Sequence[CompositeScore],
        *,
        signal_id: SignalId | None = None,
    ) -> None:
        self._lookup: dict[tuple[date, SecurityId], CompositeScore] = {
            (row.evaluation_date, row.security_id): row for row in composite_scores
        }
        self._signal_id = signal_id or SignalId("composite")
        self._metadata = SignalMetadata(
            signal_id=self._signal_id,
            signal_name="Composite Factor Score",
            signal_description="Weighted combination of normalized factor scores",
            signal_category=SignalCategory.MOMENTUM,
            signal_version="1.0",
            missing_data_policy=MissingDataPolicy.EXCLUDE_SECURITY,
            higher_is_better=True,
        )

    @property
    def signal_id(self) -> str:
        return str(self._signal_id)

    @property
    def metadata(self) -> SignalMetadata:
        return self._metadata

    def calculate(
        self,
        evaluation_date: date,
        universe: UniverseMembershipSnapshot,
        data_access: DataAccess,
    ) -> Sequence[EntrySignalResult]:
        del data_access
        results: list[EntrySignalResult] = []
        for membership in universe.memberships:
            if not membership.is_member:
                continue
            composite = self._lookup.get((evaluation_date, membership.security_id))
            if composite is None:
                continue
            results.append(
                EntrySignalResult(
                    evaluation_date=evaluation_date,
                    security_id=membership.security_id,
                    ticker=membership.ticker,
                    signal_id=self._signal_id,
                    signal_version=self._metadata.signal_version,
                    raw_signal_value=composite.composite_score,
                )
            )
        return results
