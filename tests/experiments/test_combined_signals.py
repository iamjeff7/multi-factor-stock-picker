"""Tests for combined runner signal construction."""

from backtest.experiment_config import SignalConfig
from experiments.signal_catalog import build_entry_signal, build_exit_signal


def test_build_entry_signal_accepts_signal_config() -> None:
    config = SignalConfig(
        name="momentum_12_1",
        params={"lookback_days": 252, "skip_days": 21},
    )
    signal = build_entry_signal(config)
    assert signal.signal_id == "momentum_12_1"


def test_build_exit_signal_accepts_signal_config() -> None:
    config = SignalConfig(
        name="momentum_exit_stack",
        params={"stop_pct": "0.10", "trail_pct": "0.15"},
    )
    signal = build_exit_signal(config)
    assert signal.signal_id == "momentum_exit_stack"
