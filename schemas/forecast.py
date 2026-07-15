"""Forecast schemas."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ForecastPoint:
    date: date
    value: float


@dataclass(frozen=True)
class ForecastScenario:
    name: str
    points: list[ForecastPoint]


@dataclass(frozen=True)
class ForecastResult:
    scenarios: list[ForecastScenario]
    sufficient_history: bool
    message: str
