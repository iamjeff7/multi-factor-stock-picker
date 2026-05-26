"""Point-in-time stock segment classification."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from core.types import SecurityId
from data.protocols import DataAccess
from experiments.enums import SegmentRegime, SegmentTertile
from schemas.data import PriceBar


@dataclass(frozen=True)
class SegmentLabels:
    regime: SegmentRegime
    market_cap: SegmentTertile
    volume: SegmentTertile
    volatility: SegmentTertile
    liquidity: SegmentTertile

    def key(self) -> str:
        return (
            f"{self.regime.value}|{self.market_cap.value}|{self.volume.value}|"
            f"{self.volatility.value}|{self.liquidity.value}"
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "regime": self.regime.value,
            "market_cap": self.market_cap.value,
            "volume": self.volume.value,
            "volatility": self.volatility.value,
            "liquidity": self.liquidity.value,
        }


@dataclass(frozen=True)
class SegmentObservation:
    evaluation_date: date
    security_id: SecurityId
    labels: SegmentLabels


class SegmentClassifier:
    """Assign bull/bear/sideways and cross-sectional tertiles from price bars."""

    REGIME_LOOKBACK = 63
    METRIC_LOOKBACK = 20
    SIZE_LOOKBACK = 63

    BULL_THRESHOLD = Decimal("0.05")
    BEAR_THRESHOLD = Decimal("-0.05")

    def classify_cross_section(
        self,
        data_access: DataAccess,
        security_ids: list[SecurityId],
        evaluation_date: date,
    ) -> dict[SecurityId, SegmentLabels]:
        raw: dict[SecurityId, dict[str, float | Decimal | None]] = {}
        for security_id in security_ids:
            bars = data_access.get_prices(
                security_id=security_id,
                start_date=evaluation_date - timedelta(days=400),
                end_date=evaluation_date,
                as_of_date=evaluation_date,
            )
            raw[security_id] = self._raw_features(bars, evaluation_date)

        cap_values = [row["size_proxy"] for row in raw.values() if row["size_proxy"] is not None]
        volume_values = [row["volume"] for row in raw.values() if row["volume"] is not None]
        vol_values = [row["volatility"] for row in raw.values() if row["volatility"] is not None]
        liq_values = [row["liquidity"] for row in raw.values() if row["liquidity"] is not None]

        cap_breaks = _tertile_breaks(cap_values)
        volume_breaks = _tertile_breaks(volume_values)
        vol_breaks = _tertile_breaks(vol_values)
        liq_breaks = _tertile_breaks(liq_values)

        labels: dict[SecurityId, SegmentLabels] = {}
        for security_id, features in raw.items():
            regime = _regime(features.get("regime_return"))
            labels[security_id] = SegmentLabels(
                regime=regime,
                market_cap=_tertile(features.get("size_proxy"), cap_breaks),
                volume=_tertile(features.get("volume"), volume_breaks),
                volatility=_tertile(features.get("volatility"), vol_breaks),
                liquidity=_tertile(features.get("liquidity"), liq_breaks),
            )
        return labels

    def _raw_features(
        self,
        bars: list[PriceBar],
        evaluation_date: date,
    ) -> dict[str, float | Decimal | None]:
        eligible = sorted(
            [bar for bar in bars if bar.trade_date <= evaluation_date],
            key=lambda bar: bar.trade_date,
        )
        if len(eligible) < 2:
            return {
                "regime_return": None,
                "size_proxy": None,
                "volume": None,
                "volatility": None,
                "liquidity": None,
            }

        regime_return = _return_over_lookback(eligible, self.REGIME_LOOKBACK)
        recent = eligible[-self.METRIC_LOOKBACK :]
        size_window = eligible[-self.SIZE_LOOKBACK :]

        avg_volume = statistics.fmean(float(bar.volume) for bar in recent) if recent else None
        dollar_volumes = [
            float(bar.dollar_volume or (bar.adjusted_close * Decimal(str(bar.volume))))
            for bar in recent
        ]
        avg_liquidity = statistics.fmean(dollar_volumes) if dollar_volumes else None
        size_proxies = [
            float(bar.dollar_volume or (bar.adjusted_close * Decimal(str(bar.volume))))
            for bar in size_window
        ]
        size_proxy = statistics.fmean(size_proxies) if size_proxies else None
        volatility = _realized_volatility(recent)

        return {
            "regime_return": regime_return,
            "size_proxy": Decimal(str(size_proxy)) if size_proxy is not None else None,
            "volume": Decimal(str(avg_volume)) if avg_volume is not None else None,
            "volatility": Decimal(str(volatility)) if volatility is not None else None,
            "liquidity": Decimal(str(avg_liquidity)) if avg_liquidity is not None else None,
        }


def _return_over_lookback(bars: list[PriceBar], lookback: int) -> Decimal | None:
    if len(bars) <= lookback:
        return None
    start = bars[-lookback - 1].adjusted_close
    end = bars[-1].adjusted_close
    if start <= Decimal("0"):
        return None
    return (end / start) - Decimal("1")


def _realized_volatility(bars: list[PriceBar]) -> float | None:
    if len(bars) < 2:
        return None
    returns: list[float] = []
    for index in range(1, len(bars)):
        prev = bars[index - 1].adjusted_close
        curr = bars[index].adjusted_close
        if prev <= Decimal("0"):
            continue
        returns.append(float((curr / prev) - Decimal("1")))
    if len(returns) < 2:
        return None
    return statistics.pstdev(returns) * math.sqrt(252)


def _tertile_breaks(values: list[float | Decimal]) -> tuple[float, float] | None:
    if len(values) < 3:
        return None
    floats = sorted(float(value) for value in values)
    lower_index = max(0, len(floats) // 3 - 1)
    upper_index = min(len(floats) - 1, (2 * len(floats)) // 3)
    return floats[lower_index], floats[upper_index]


def _tertile(
    value: float | Decimal | None,
    breaks: tuple[float, float] | None,
) -> SegmentTertile:
    if value is None or breaks is None:
        return SegmentTertile.MEDIUM
    numeric = float(value)
    lower, upper = breaks
    if numeric <= lower:
        return SegmentTertile.LOW
    if numeric >= upper:
        return SegmentTertile.HIGH
    return SegmentTertile.MEDIUM


def _regime(regime_return: Decimal | None) -> SegmentRegime:
    if regime_return is None:
        return SegmentRegime.SIDEWAYS
    if regime_return >= SegmentClassifier.BULL_THRESHOLD:
        return SegmentRegime.BULL
    if regime_return <= SegmentClassifier.BEAR_THRESHOLD:
        return SegmentRegime.BEAR
    return SegmentRegime.SIDEWAYS
