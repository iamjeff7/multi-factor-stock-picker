"""Parquet serialization helpers for result records."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from math import isnan
from pathlib import Path
from typing import TypeVar

import pandas as pd
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def records_to_dataframe(rows: Sequence[BaseModel]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    serialized = [_serialize_record(row.model_dump(mode="json")) for row in rows]
    return pd.DataFrame(serialized)


def dataframe_to_records(df: pd.DataFrame, model: type[T]) -> list[T]:
    if df.empty:
        return []
    records: list[T] = []
    for row in df.to_dict(orient="records"):
        records.append(model.model_validate(_deserialize_record(row)))
    return records


def write_records(path: Path, rows: Sequence[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = records_to_dataframe(rows)
    df.to_parquet(path, index=False)


def read_records(path: Path, model: type[T]) -> list[T]:
    df = pd.read_parquet(path)
    return dataframe_to_records(df, model)


def write_record(path: Path, row: BaseModel) -> None:
    write_records(path, [row])


def read_record(path: Path, model: type[T]) -> T | None:
    records = read_records(path, model)
    if not records:
        return None
    return records[0]


def _serialize_record(value: object) -> object:
    if isinstance(value, dict):
        return {key: _serialize_record(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_record(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _deserialize_record(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, float) and isnan(value):
        return None
    if isinstance(value, dict):
        return {key: _deserialize_record(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_deserialize_record(item) for item in value]
    if isinstance(value, str) and _looks_like_json_dict(value):
        return json.loads(value)
    return value


def _looks_like_json_dict(value: str) -> bool:
    return value.startswith("{") and value.endswith("}")
