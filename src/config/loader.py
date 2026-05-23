"""YAML configuration loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from core.exceptions import ConfigurationError

T = TypeVar("T", bound=BaseModel)


def load_yaml_config(path: Path, model: type[T]) -> T:
    """Load and validate a YAML file into a Pydantic model."""
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")

    with path.open(encoding="utf-8") as handle:
        raw: Any = yaml.safe_load(handle)

    if raw is None:
        raw = {}

    if not isinstance(raw, dict):
        raise ConfigurationError(f"Configuration file must contain a mapping: {path}")

    return model.model_validate(raw)
