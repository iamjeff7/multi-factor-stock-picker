#!/usr/bin/env python3
"""Download Mag 7 stock data from yfinance into Parquet raw dataset format."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import yaml

MAG7_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
DEFAULT_START = "2018-01-01"


def _security_id(ticker: str) -> str:
    return f"SEC_{ticker}"


def _map_exchange(raw: str | None) -> str:
    if not raw:
        return "NASDAQ"
    normalized = raw.upper()
    mapping = {
        "NMS": "NASDAQ",
        "NCM": "NASDAQ",
        "NGM": "NASDAQ",
        "NYQ": "NYSE",
        "NYS": "NYSE",
        "ASE": "NYSE_AMERICAN",
        "AMEX": "NYSE_AMERICAN",
    }
    if normalized in mapping:
        return mapping[normalized]
    if "NASDAQ" in normalized:
        return "NASDAQ"
    if "NYSE AMERICAN" in normalized or "AMEX" in normalized:
        return "NYSE_AMERICAN"
    if "NYSE" in normalized:
        return "NYSE"
    return "NASDAQ"


def download_dataset(output_dir: Path, start: str, end: str | None) -> None:
    import yfinance as yf

    output_dir.mkdir(parents=True, exist_ok=True)

    price_rows: list[dict[str, object]] = []
    security_rows: list[dict[str, object]] = []
    action_rows: list[dict[str, object]] = []

    for ticker in MAG7_TICKERS:
        symbol = yf.Ticker(ticker)
        history = symbol.history(start=start, end=end, auto_adjust=False)
        if history.empty:
            raise RuntimeError(f"No price history returned for {ticker}")

        info = symbol.info
        security_id = _security_id(ticker)
        first_date = history.index.min().date()
        last_date = history.index.max().date()

        security_rows.append(
            {
                "security_id": security_id,
                "ticker": ticker,
                "permanent_security_id": security_id,
                "company_name": info.get("longName") or ticker,
                "exchange": _map_exchange(info.get("exchange")),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "as_of_date": first_date,
            }
        )
        if last_date != first_date:
            security_rows.append(
                {
                    "security_id": security_id,
                    "ticker": ticker,
                    "permanent_security_id": security_id,
                    "company_name": info.get("longName") or ticker,
                    "exchange": _map_exchange(info.get("exchange")),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "as_of_date": last_date,
                }
            )

        for ts, row in history.iterrows():
            trade_date = ts.date()
            close = Decimal(str(row["Close"]))
            volume = int(row["Volume"])
            price_rows.append(
                {
                    "security_id": security_id,
                    "trade_date": trade_date,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "adjusted_close": float(row["Adj Close"]),
                    "volume": volume,
                    "dollar_volume": float(close * volume),
                }
            )

        splits = symbol.splits
        for ts, ratio in splits.items():
            action_rows.append(
                {
                    "security_id": security_id,
                    "action_date": ts.date(),
                    "action_type": "SPLIT" if float(ratio) > 1 else "REVERSE_SPLIT",
                    "ratio": float(ratio),
                    "amount": None,
                }
            )

        dividends = symbol.dividends
        for ts, amount in dividends.items():
            action_rows.append(
                {
                    "security_id": security_id,
                    "action_date": ts.date(),
                    "action_type": "CASH_DIVIDEND",
                    "ratio": None,
                    "amount": float(amount),
                }
            )

    pd.DataFrame(security_rows).to_parquet(output_dir / "securities.parquet", index=False)
    pd.DataFrame(price_rows).to_parquet(output_dir / "prices.parquet", index=False)
    pd.DataFrame(action_rows).to_parquet(output_dir / "corporate_actions.parquet", index=False)
    pd.DataFrame(
        columns=["security_id", "delisting_date", "delisting_reason"]
    ).to_parquet(output_dir / "delistings.parquet", index=False)

    manifest = {
        "data_version": "mag7_001",
        "creation_timestamp": datetime.now(tz=UTC).isoformat(),
        "description": "Mag 7 US equities downloaded via yfinance (demo dataset)",
        "tickers": MAG7_TICKERS,
    }
    with (output_dir / "manifest.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(manifest, handle, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Mag 7 dataset to Parquet")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/mag7_001"),
        help="Output directory for raw dataset",
    )
    parser.add_argument("--start", default=DEFAULT_START, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="End date YYYY-MM-DD (optional)")
    args = parser.parse_args()
    download_dataset(args.output, args.start, args.end)
    print(f"Dataset written to {args.output.resolve()}")


if __name__ == "__main__":
    main()
