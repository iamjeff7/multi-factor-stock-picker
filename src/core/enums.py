"""Shared enumerations."""

from enum import StrEnum


class Exchange(StrEnum):
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    NYSE_AMERICAN = "NYSE_AMERICAN"


class SecurityType(StrEnum):
    COMMON_STOCK = "COMMON_STOCK"


class Frequency(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"


class ExperimentType(StrEnum):
    SINGLE_FACTOR = "SINGLE_FACTOR"
    MULTI_FACTOR = "MULTI_FACTOR"
    EXIT_SIGNAL = "EXIT_SIGNAL"
    FULL_STRATEGY = "FULL_STRATEGY"


class ExperimentStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PositionStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ExecutionPrice(StrEnum):
    NEXT_OPEN = "NEXT_OPEN"
    NEXT_CLOSE = "NEXT_CLOSE"
    NEXT_VWAP = "NEXT_VWAP"


class PortfolioMode(StrEnum):
    SINGLE = "SINGLE"
    TOP_N = "TOP_N"
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    CUSTOM = "CUSTOM"


class PositionSizeMethod(StrEnum):
    FIXED_DOLLAR = "FIXED_DOLLAR"
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    RISK_BASED = "RISK_BASED"
    VOLATILITY_BASED = "VOLATILITY_BASED"


class RebalanceFrequency(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class SamplePeriod(StrEnum):
    IN_SAMPLE = "IS"
    OUT_OF_SAMPLE = "OOS"
    FULL = "FULL"


class ResearchMode(StrEnum):
    PRODUCTION = "PRODUCTION"
    DEMO = "DEMO"
    TEST = "TEST"


class ResearchPhase(StrEnum):
    DISCOVERY = "DISCOVERY"
    VALIDATION = "VALIDATION"


class SampleScope(StrEnum):
    IN_SAMPLE = "IS"
    OUT_OF_SAMPLE = "OOS"
    FULL = "FULL"
