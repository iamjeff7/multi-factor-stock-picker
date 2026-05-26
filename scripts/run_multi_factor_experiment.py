#!/usr/bin/env python3
"""Deprecated wrapper — use scripts/run_experiment.py instead."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deprecated: use scripts/run_experiment.py",
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=ROOT / "tests" / "fixtures" / "data" / "mag7")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    print("Note: run_multi_factor_experiment.py is deprecated; invoking run_experiment.py")
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_experiment.py"),
        "--config",
        str(args.config),
        "--data",
        str(args.data),
        "--output-dir",
        str(args.output_dir),
    ]
    raise SystemExit(subprocess.call(command))


if __name__ == "__main__":
    main()
