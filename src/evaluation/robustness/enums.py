"""Entry robustness enumerations."""

from enum import StrEnum


class RobustnessClassification(StrEnum):
    EXCEPTIONAL = "EXCEPTIONAL"
    STRONG = "STRONG"
    GOOD = "GOOD"
    ACCEPTABLE = "ACCEPTABLE"
    WEAK = "WEAK"
    REJECT = "REJECT"
