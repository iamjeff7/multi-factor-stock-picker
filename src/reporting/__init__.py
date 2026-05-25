"""Experiment reporting and result persistence."""

from reporting.aggregators import aggregate_stock_summaries
from reporting.experiment_aggregators import aggregate_experiment_summary
from reporting.generators.experiment_report import ExperimentReportGenerator
from reporting.layout import ResultLayout
from reporting.manifest import build_backtest_report_manifest
from reporting.protocols import ResultStore, SchemaValidator
from reporting.stores import InMemoryResultStore, ParquetResultStore, ValidatingResultStore
from reporting.validator import ResultSchemaValidator

__all__ = [
    "ResultLayout",
    "ResultSchemaValidator",
    "ResultStore",
    "SchemaValidator",
    "InMemoryResultStore",
    "ParquetResultStore",
    "ValidatingResultStore",
    "aggregate_stock_summaries",
    "aggregate_experiment_summary",
    "build_backtest_report_manifest",
    "ExperimentReportGenerator",
]
