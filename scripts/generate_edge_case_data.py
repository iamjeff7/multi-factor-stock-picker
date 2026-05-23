#!/usr/bin/env python3
"""Generate synthetic edge-case dataset for universe and validation tests."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yaml


def _daily_bars(
    security_id: str,
    start: date,
    days: int,
    *,
    close: float = 100.0,
    volume: int = 1_000_000,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset in range(days):
        trade_date = start + timedelta(days=offset)
        if trade_date.weekday() >= 5:
            continue
        rows.append(
            {
                "security_id": security_id,
                "trade_date": trade_date,
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "adjusted_close": close,
                "volume": volume,
                "dollar_volume": close * volume,
            }
        )
    return rows


def generate(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    start = date(2020, 1, 1)

    price_rows: list[dict[str, object]] = []
    price_rows.extend(_daily_bars("SEC_NORMAL", start, 1300, close=50.0, volume=2_000_000))
    price_rows.extend(_daily_bars("SEC_ILLIQ", start, 1300, close=50.0, volume=1_000))
    price_rows.extend(_daily_bars("SEC_DELIST", start, 1300, close=50.0, volume=2_000_000))
    price_rows.extend(_daily_bars("SEC_IPO", date(2024, 1, 1), 400, close=50.0, volume=2_000_000))

    securities = [
        {
            "security_id": "SEC_NORMAL",
            "ticker": "NORMAL",
            "permanent_security_id": "SEC_NORMAL",
            "company_name": "Normal Corp",
            "exchange": "NASDAQ",
            "sector": "Tech",
            "industry": "Software",
            "as_of_date": date(2023, 12, 29),
        },
        {
            "security_id": "SEC_ILLIQ",
            "ticker": "ILLIQ",
            "permanent_security_id": "SEC_ILLIQ",
            "company_name": "Illiquid Corp",
            "exchange": "NASDAQ",
            "sector": "Tech",
            "industry": "Software",
            "as_of_date": date(2023, 12, 29),
        },
        {
            "security_id": "SEC_DELIST",
            "ticker": "DELIST",
            "permanent_security_id": "SEC_DELIST",
            "company_name": "Delist Corp",
            "exchange": "NASDAQ",
            "sector": "Tech",
            "industry": "Software",
            "as_of_date": date(2023, 12, 29),
        },
        {
            "security_id": "SEC_IPO",
            "ticker": "IPO",
            "permanent_security_id": "SEC_IPO",
            "company_name": "IPO Corp",
            "exchange": "NASDAQ",
            "sector": "Tech",
            "industry": "Software",
            "as_of_date": date(2024, 3, 1),
        },
    ]

    delistings = [
        {
            "security_id": "SEC_DELIST",
            "delisting_date": date(2023, 6, 1),
            "delisting_reason": "ACQUIRED",
        }
    ]

    pd.DataFrame(securities).to_parquet(output_dir / "securities.parquet", index=False)
    pd.DataFrame(price_rows).to_parquet(output_dir / "prices.parquet", index=False)
    pd.DataFrame(
        columns=["security_id", "action_date", "action_type", "ratio", "amount"]
    ).to_parquet(output_dir / "corporate_actions.parquet", index=False)
    pd.DataFrame(delistings).to_parquet(output_dir / "delistings.parquet", index=False)

    manifest = {
        "data_version": "edge_cases_001",
        "creation_timestamp": "2026-01-01T00:00:00+00:00",
        "description": "Synthetic edge cases for universe filtering tests",
        "tickers": ["NORMAL", "ILLIQ", "DELIST", "IPO"],
    }
    with (output_dir / "manifest.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(manifest, handle, sort_keys=False)


if __name__ == "__main__":
    generate(Path("tests/fixtures/data/edge_cases"))
