"""Shared fixtures for factor performance tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from core.types import SecurityId, SignalId, Ticker
from schemas.factors import FactorScore
from schemas.ic import ForwardReturn


@pytest.fixture
def evaluation_date() -> date:
    return date(2020, 6, 1)


@pytest.fixture
def sample_scores(evaluation_date: date) -> list[FactorScore]:
    rows: list[FactorScore] = []
    for index in range(7):
        rows.append(
            FactorScore(
                evaluation_date=evaluation_date,
                security_id=SecurityId(f"SEC_{index}"),
                ticker=Ticker(f"T{index}"),
                signal_id=SignalId("momentum_12_1"),
                factor_score=Decimal(index) / Decimal("6"),
                factor_rank=Decimal(index + 1),
            )
        )
    return rows


@pytest.fixture
def sample_forward_returns(evaluation_date: date) -> list[ForwardReturn]:
    rows: list[ForwardReturn] = []
    for index in range(7):
        rows.append(
            ForwardReturn(
                evaluation_date=evaluation_date,
                security_id=SecurityId(f"SEC_{index}"),
                horizon=63,
                forward_return=Decimal("0.01") * Decimal(index + 1),
            )
        )
    return rows
