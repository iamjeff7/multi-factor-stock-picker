"""Tests for unified cross-section factor evaluation."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from backtest.factor_evaluation_config import FactorEvaluationSettings
from config.loader import load_yaml_config
from data.loaders import ParquetLoader
from data.store import InMemoryDataStore
from experiments.config import UnifiedExperimentConfig
from experiments.entry_runner import EntryExperimentRunner
from experiments.evaluation.config_adapter import resolve_factor_evaluation_settings
from experiments.exit_runner import ExitExperimentRunner


@pytest.fixture
def mag7_store() -> InMemoryDataStore:
    root = Path(__file__).resolve().parents[2]
    dataset = ParquetLoader().load(root / "tests" / "fixtures" / "data" / "mag7")
    return InMemoryDataStore(dataset)


def test_resolve_factor_evaluation_settings_uses_universe_size_for_mag7() -> None:
    settings = resolve_factor_evaluation_settings(
        FactorEvaluationSettings(minimum_security_count=30, horizons=[21, 63], primary_horizon=63),
        security_count=7,
        exit_horizon_months=3,
    )
    assert settings.minimum_security_count == 7
    assert settings.primary_horizon == 63
    assert 63 in settings.horizons


def test_entry_demo_report_includes_cross_section_and_real_robustness(
    mag7_store: InMemoryDataStore,
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    config = load_yaml_config(
        root / "configs" / "experiments" / "entry_demo.yaml",
        UnifiedExperimentConfig,
    )
    report_path = EntryExperimentRunner().run(
        config,
        mag7_store,
        output_dir=tmp_path,
        reference_date=date(2026, 5, 26),
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    factor_results = payload["factor_results"]
    assert factor_results

    completed = [
        row for row in factor_results if row["cross_section"]["status"] == "completed"
    ]
    assert completed, "expected at least one completed cross-section evaluation"

    robustness_scores = {
        row["aggregate"]["robustness"]["overall_robustness_score"]
        for row in completed
        if row["aggregate"]["robustness"]["overall_robustness_score"] is not None
    }
    assert robustness_scores, "expected real robustness scores"
    assert robustness_scores != {"0.70"}, "robustness should not use placeholder score"

    first = completed[0]
    assert first["cross_section"]["factor_ic"]["available"] is True
    assert first["cross_section"]["entry_robustness"]["available"] is True

    rankings_path = report_path.parent.parent / "rankings" / "entry_top_factors.json"
    rankings = json.loads(rankings_path.read_text(encoding="utf-8"))
    first_segment = next(iter(rankings["segments"].values()))
    first_factor = first_segment["factors"][0]
    assert "evaluation_summary" in first_factor["score_breakdown"]


def test_exit_demo_report_includes_exit_robustness_and_real_scores(
    mag7_store: InMemoryDataStore,
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    config = load_yaml_config(
        root / "configs" / "experiments" / "exit_demo.yaml",
        UnifiedExperimentConfig,
    )
    report_path = ExitExperimentRunner().run(
        config,
        mag7_store,
        output_dir=tmp_path,
        reference_date=date(2026, 5, 26),
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    factor_results = payload["factor_results"]
    assert factor_results

    completed = [
        row for row in factor_results if row["exit_robustness"]["status"] == "completed"
    ]
    assert completed, "expected at least one completed exit robustness evaluation"

    robustness_scores = {
        row["aggregate"]["robustness"]["overall_robustness_score"]
        for row in completed
        if row["aggregate"]["robustness"]["overall_robustness_score"] is not None
    }
    assert robustness_scores, "expected real exit robustness scores"
    assert robustness_scores != {"0.55"}, "robustness should not use placeholder score"

    first = completed[0]
    assert first["exit_robustness"]["exit_robustness"]["available"] is True

    rankings_path = report_path.parent.parent / "rankings" / "exit_top_factors.json"
    rankings = json.loads(rankings_path.read_text(encoding="utf-8"))
    first_segment = next(iter(rankings["segments"].values()))
    first_factor = first_segment["factors"][0]
    assert "evaluation_summary" in first_factor["score_breakdown"]
