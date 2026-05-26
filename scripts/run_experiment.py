#!/usr/bin/env python3
"""Run unified entry, exit, or entry+exit experiments."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config.loader import load_yaml_config  # noqa: E402
from data.loaders import ParquetLoader  # noqa: E402
from data.store import InMemoryDataStore  # noqa: E402
from experiments.config import UnifiedExperimentConfig  # noqa: E402
from experiments.runner import UnifiedExperimentRunner  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a unified experiment")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to experiment YAML config",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "data" / "mag7",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results",
    )
    parser.add_argument(
        "--reference-date",
        type=_parse_date,
        default=None,
        help="Reference date for demo preset resolution (default: today)",
    )
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"Dataset not found: {args.data}")

    config = load_yaml_config(args.config, UnifiedExperimentConfig)
    dataset = ParquetLoader().load(args.data)
    store = InMemoryDataStore(dataset)
    runner = UnifiedExperimentRunner()
    report_path = runner.run(
        config,
        store,
        output_dir=args.output_dir,
        reference_date=args.reference_date,
    )
    print(f"Report: {report_path}")


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


if __name__ == "__main__":
    main()
