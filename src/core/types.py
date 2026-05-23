"""Canonical identifier and alias types."""

from datetime import date, datetime
from typing import NewType

SecurityId = NewType("SecurityId", str)
Ticker = NewType("Ticker", str)
ExperimentId = NewType("ExperimentId", str)
SignalId = NewType("SignalId", str)
PositionId = NewType("PositionId", str)
TradeId = NewType("TradeId", str)
DataVersion = NewType("DataVersion", str)
UniverseVersion = NewType("UniverseVersion", str)
ConfigurationHash = NewType("ConfigurationHash", str)

EvaluationDate = date
ExecutionTimestamp = datetime
