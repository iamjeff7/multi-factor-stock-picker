#!/usr/bin/env python3
"""Run a cross-sectional single-factor experiment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest.experiment_config import SingleFactorExperimentConfig  # noqa: E402
from backtest.experiment_runner import SingleFactorExperimentRunner  # noqa: E402
from backtest.signal_factory import build_entry_signal, build_exit_signal  # noqa: E402
from config.loader import load_yaml_config  # noqa: E402
from data.loaders import ParquetLoader  # noqa: E402
from data.store import InMemoryDataStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single-factor experiment")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "mag7_stub_single_factor.yaml",
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
        help="Directory for persisted experiment artifacts",
    )
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"Dataset not found: {args.data}")

    config = load_yaml_config(args.config, SingleFactorExperimentConfig)
    dataset = ParquetLoader().load(args.data)
    store = InMemoryDataStore(dataset)
    entry_signal = build_entry_signal(config.entry_signal)
    exit_signal = build_exit_signal(config.exit_signal)

    runner = SingleFactorExperimentRunner()
    result = runner.run(
        config=config,
        data_access=store,
        entry_signal=entry_signal,
        exit_signal=exit_signal,
        output_dir=args.output_dir,
    )

    summary = result.experiment_summary
    print(f"Experiment: {result.experiment_id}")
    print(f"Securities completed: {summary.securities_completed}/{summary.securities_requested}")
    print(f"Securities skipped: {summary.securities_skipped}")
    print(f"Mean stock return: {summary.mean_stock_return}")
    print(f"Pooled win rate: {summary.win_rate}")
    print(f"Total trades: {summary.number_of_trades}")
    if result.report_path is not None:
        print(f"Report: {result.report_path}")
    print(f"Results dir: {args.output_dir / str(result.experiment_id)}")


if __name__ == "__main__":
    main()
