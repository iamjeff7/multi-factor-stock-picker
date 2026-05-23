"""Corporate action price adjustment."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from schemas.data import CorporateAction, PriceBar


class CorporateActionAdjuster:
    """Applies corporate actions to derive adjusted price series from raw closes."""

    def adjust_prices(
        self,
        bars: Sequence[PriceBar],
        actions: Sequence[CorporateAction],
    ) -> list[PriceBar]:
        if not bars:
            return []

        sorted_bars = sorted(bars, key=lambda bar: bar.trade_date)
        split_actions = sorted(
            [
                action
                for action in actions
                if action.action_type in ("SPLIT", "REVERSE_SPLIT") and action.ratio is not None
            ],
            key=lambda action: action.action_date,
            reverse=True,
        )

        adjusted: list[PriceBar] = []
        factor = Decimal("1")
        action_index = 0

        for bar in reversed(sorted_bars):
            while (
                action_index < len(split_actions)
                and bar.trade_date < split_actions[action_index].action_date
            ):
                ratio = split_actions[action_index].ratio
                if ratio is not None and ratio > 0:
                    factor /= ratio
                action_index += 1

            adjusted.append(
                bar.model_copy(
                    update={"adjusted_close": (bar.close * factor).quantize(Decimal("0.0001"))}
                )
            )

        adjusted.reverse()
        return adjusted
