"""Catalog of real entry/exit signals and parameter variants for sweeps."""

from __future__ import annotations

from dataclasses import dataclass

from backtest.experiment_config import SignalConfig
from entry_signals.protocols import EntrySignal
from exit_signals.protocols import ExitSignal


@dataclass(frozen=True)
class SignalVariant:
    signal_id: str
    variant_id: str
    config: SignalConfig


REAL_ENTRY_SIGNAL_NAMES = frozenset({"momentum_12_1", "momentum_6_1"})
REAL_EXIT_SIGNAL_NAMES = frozenset({"stop_loss", "trailing_stop", "momentum_exit_stack"})


def list_entry_variants() -> list[SignalVariant]:
    variants: list[SignalVariant] = []
    for lookback, skip, name in (
        (252, 21, "momentum_12_1"),
        (126, 21, "momentum_6_1"),
    ):
        variants.append(
            SignalVariant(
                signal_id=name,
                variant_id=f"lookback_{lookback}_skip_{skip}",
                config=SignalConfig(
                    name=name,
                    params={"lookback_days": lookback, "skip_days": skip},
                ),
            )
        )
        variants.append(
            SignalVariant(
                signal_id=name,
                variant_id=f"lookback_{int(lookback * 0.8)}_skip_{skip}",
                config=SignalConfig(
                    name=name,
                    params={"lookback_days": int(lookback * 0.8), "skip_days": skip},
                ),
            )
        )
    return variants


def list_exit_variants() -> list[SignalVariant]:
    variants: list[SignalVariant] = []
    for stop_pct in ("0.08", "0.10", "0.12"):
        variants.append(
            SignalVariant(
                signal_id="stop_loss",
                variant_id=f"stop_{stop_pct}",
                config=SignalConfig(name="stop_loss", params={"stop_pct": stop_pct}),
            )
        )
    for trail_pct in ("0.10", "0.15", "0.20"):
        variants.append(
            SignalVariant(
                signal_id="trailing_stop",
                variant_id=f"trail_{trail_pct}",
                config=SignalConfig(name="trailing_stop", params={"trail_pct": trail_pct}),
            )
        )
    for stop_pct, trail_pct in (("0.10", "0.15"), ("0.08", "0.12")):
        variants.append(
            SignalVariant(
                signal_id="momentum_exit_stack",
                variant_id=f"stop_{stop_pct}_trail_{trail_pct}",
                config=SignalConfig(
                    name="momentum_exit_stack",
                    params={"stop_pct": stop_pct, "trail_pct": trail_pct},
                ),
            )
        )
    return variants


def build_entry_signal(variant: SignalVariant | SignalConfig) -> EntrySignal:
    from backtest.signal_factory import build_entry_signal as _build

    config = variant.config if isinstance(variant, SignalVariant) else variant
    return _build(config)


def build_exit_signal(variant: SignalVariant | SignalConfig) -> ExitSignal:
    from backtest.signal_factory import build_exit_signal as _build

    config = variant.config if isinstance(variant, SignalVariant) else variant
    return _build(config)


def fixed_period_exit_config(months: int) -> SignalConfig:
    return SignalConfig(name="fixed_period_exit", params={"holding_months": months})


def scheduled_entry_config(cadence: str) -> SignalConfig:
    return SignalConfig(name="scheduled_entry", params={"cadence": cadence})


def bottom_entry_config() -> SignalConfig:
    return SignalConfig(name="bottom_entry", params={"price_field": "close"})
