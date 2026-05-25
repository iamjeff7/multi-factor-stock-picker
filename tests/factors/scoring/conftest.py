"""Shared helpers for factor scoring tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.types import SecurityId, SignalId, Ticker
from schemas.entry import EntrySignalResult


def make_entry_signal_result(
    *,
    security_id: str,
    ticker: str,
    raw_value: Decimal | None,
    evaluation_date: date = date(2020, 1, 31),
    signal_id: str = "momentum_12m",
) -> EntrySignalResult:
    return EntrySignalResult(
        evaluation_date=evaluation_date,
        security_id=SecurityId(security_id),
        ticker=Ticker(ticker),
        signal_id=SignalId(signal_id),
        signal_version="1.0",
        raw_signal_value=raw_value,
    )


def make_cross_section(
    values: dict[str, Decimal | None],
    *,
    evaluation_date: date = date(2020, 1, 31),
    signal_id: str = "momentum_12m",
) -> list[EntrySignalResult]:
    return [
        make_entry_signal_result(
            security_id=security_id,
            ticker=security_id,
            raw_value=raw_value,
            evaluation_date=evaluation_date,
            signal_id=signal_id,
        )
        for security_id, raw_value in values.items()
    ]


def make_minimum_cross_section(
    count: int,
    *,
    evaluation_date: date = date(2020, 1, 31),
    signal_id: str = "momentum_12m",
) -> list[EntrySignalResult]:
    return [
        make_entry_signal_result(
            security_id=f"{index:03d}",
            ticker=f"T{index:03d}",
            raw_value=Decimal(index),
            evaluation_date=evaluation_date,
            signal_id=signal_id,
        )
        for index in range(count)
    ]
