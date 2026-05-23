"""Parquet dataset loader."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from core.exceptions import ConfigurationError
from core.types import SecurityId, Ticker
from data.loaders.dataset import LoadedDataset
from data.loaders.manifest import DatasetManifest
from schemas.data import (
    CorporateAction,
    DelistingInfo,
    FundamentalRecord,
    PriceBar,
    SecurityMetadata,
)


class ParquetLoader:
    """Loads raw Parquet tables from a dataset directory."""

    REQUIRED_FILES = ("securities.parquet", "prices.parquet", "corporate_actions.parquet")

    def load(self, raw_dir: Path) -> LoadedDataset:
        raw_dir = raw_dir.resolve()
        if not raw_dir.is_dir():
            raise ConfigurationError(f"Dataset directory not found: {raw_dir}")

        for filename in self.REQUIRED_FILES:
            if not (raw_dir / filename).exists():
                raise ConfigurationError(f"Missing required file: {raw_dir / filename}")

        manifest = DatasetManifest.load(raw_dir)
        dataset = LoadedDataset(manifest=manifest)

        securities_df = pd.read_parquet(raw_dir / "securities.parquet")
        prices_df = pd.read_parquet(raw_dir / "prices.parquet")
        actions_df = pd.read_parquet(raw_dir / "corporate_actions.parquet")

        dataset.metadata = self._load_metadata(securities_df)
        dataset.prices = self._load_prices(prices_df)
        dataset.corporate_actions = self._load_corporate_actions(actions_df)

        fundamentals_path = raw_dir / "fundamentals.parquet"
        if fundamentals_path.exists():
            dataset.fundamentals = self._load_fundamentals(pd.read_parquet(fundamentals_path))

        delistings_path = raw_dir / "delistings.parquet"
        if delistings_path.exists():
            dataset.delistings = self._load_delistings(pd.read_parquet(delistings_path))

        return dataset

    def _load_prices(self, df: pd.DataFrame) -> dict[SecurityId, list[PriceBar]]:
        required = {
            "security_id",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
        }
        missing = required - set(df.columns)
        if missing:
            raise ConfigurationError(f"prices.parquet missing columns: {sorted(missing)}")

        result: dict[SecurityId, list[PriceBar]] = {}
        for security_id, group in df.groupby("security_id", sort=True):
            bars = [
                PriceBar(
                    trade_date=_to_date(row["trade_date"]),
                    open=_to_decimal(row["open"]),
                    high=_to_decimal(row["high"]),
                    low=_to_decimal(row["low"]),
                    close=_to_decimal(row["close"]),
                    adjusted_close=_to_decimal(row["adjusted_close"]),
                    volume=int(row["volume"]),
                    vwap=_optional_decimal(row.get("vwap")),
                    dollar_volume=_optional_decimal(row.get("dollar_volume")),
                )
                for _, row in group.sort_values("trade_date").iterrows()
            ]
            result[SecurityId(str(security_id))] = bars
        return result

    def _load_metadata(self, df: pd.DataFrame) -> dict[SecurityId, list[SecurityMetadata]]:
        required = {
            "security_id",
            "ticker",
            "permanent_security_id",
            "company_name",
            "exchange",
            "as_of_date",
        }
        missing = required - set(df.columns)
        if missing:
            raise ConfigurationError(f"securities.parquet missing columns: {sorted(missing)}")

        result: dict[SecurityId, list[SecurityMetadata]] = {}
        for security_id, group in df.groupby("security_id", sort=True):
            rows = [
                SecurityMetadata(
                    security_id=SecurityId(str(row["security_id"])),
                    ticker=Ticker(str(row["ticker"])),
                    permanent_security_id=str(row["permanent_security_id"]),
                    company_name=str(row["company_name"]),
                    exchange=str(row["exchange"]),
                    sector=_optional_str(row.get("sector")),
                    industry=_optional_str(row.get("industry")),
                    as_of_date=_to_date(row["as_of_date"]),
                )
                for _, row in group.sort_values("as_of_date").iterrows()
            ]
            result[SecurityId(str(security_id))] = rows
        return result

    def _load_corporate_actions(self, df: pd.DataFrame) -> dict[SecurityId, list[CorporateAction]]:
        if df.empty:
            return {}
        required = {"security_id", "action_date", "action_type"}
        missing = required - set(df.columns)
        if missing:
            raise ConfigurationError(
                f"corporate_actions.parquet missing columns: {sorted(missing)}"
            )

        result: dict[SecurityId, list[CorporateAction]] = {}
        for security_id, group in df.groupby("security_id", sort=True):
            actions = [
                CorporateAction(
                    security_id=SecurityId(str(row["security_id"])),
                    action_date=_to_date(row["action_date"]),
                    action_type=row["action_type"],
                    ratio=_optional_decimal(row.get("ratio")),
                    amount=_optional_decimal(row.get("amount")),
                )
                for _, row in group.sort_values("action_date").iterrows()
            ]
            result[SecurityId(str(security_id))] = actions
        return result

    def _load_fundamentals(self, df: pd.DataFrame) -> dict[SecurityId, list[FundamentalRecord]]:
        if df.empty:
            return {}
        required = {
            "security_id",
            "metric_name",
            "reporting_period_end",
            "filing_date",
            "availability_date",
            "value",
        }
        missing = required - set(df.columns)
        if missing:
            raise ConfigurationError(f"fundamentals.parquet missing columns: {sorted(missing)}")

        result: dict[SecurityId, list[FundamentalRecord]] = {}
        for security_id, group in df.groupby("security_id", sort=True):
            records = [
                FundamentalRecord(
                    security_id=SecurityId(str(row["security_id"])),
                    metric_name=str(row["metric_name"]),
                    reporting_period_end=_to_date(row["reporting_period_end"]),
                    filing_date=_to_date(row["filing_date"]),
                    availability_date=_to_date(row["availability_date"]),
                    value=_optional_decimal(row.get("value")),
                )
                for _, row in group.iterrows()
            ]
            result[SecurityId(str(security_id))] = records
        return result

    def _load_delistings(self, df: pd.DataFrame) -> dict[SecurityId, DelistingInfo]:
        if df.empty:
            return {}
        required = {"security_id", "delisting_date", "delisting_reason"}
        missing = required - set(df.columns)
        if missing:
            raise ConfigurationError(f"delistings.parquet missing columns: {sorted(missing)}")

        result: dict[SecurityId, DelistingInfo] = {}
        for _, row in df.iterrows():
            sid = SecurityId(str(row["security_id"]))
            result[sid] = DelistingInfo(
                security_id=sid,
                delisting_date=_to_date(row["delisting_date"]),
                delisting_reason=str(row["delisting_reason"]),
            )
        return result


def _to_date(value: object) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    ts = pd.Timestamp(str(value))
    return date(ts.year, ts.month, ts.day)


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _optional_decimal(value: object | None) -> Decimal | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return _to_decimal(value)


def _optional_str(value: object | None) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return str(value)
