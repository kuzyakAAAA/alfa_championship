"""Tests for deterministic revenue forecasting."""

import pandas as pd

from services.forecast_service import build_revenue_forecast


def test_forecast_returns_three_scenarios() -> None:
    frame = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-15", "2026-02-15", "2026-03-15", "2026-04-15"]),
        "operation_type": ["income"] * 4,
        "amount": [100.0, 120.0, 140.0, 160.0],
    })
    result = build_revenue_forecast(frame)
    assert result.sufficient_history
    assert [scenario.name for scenario in result.scenarios] == ["Пессимистичный", "Базовый", "Оптимистичный"]
    assert all(len(scenario.points) == 3 for scenario in result.scenarios)
    assert result.scenarios[1].points[0].value == 180.0


def test_forecast_reports_insufficient_history() -> None:
    frame = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-15", "2026-02-15"]),
        "operation_type": ["income", "income"],
        "amount": [100.0, 120.0],
    })
    assert not build_revenue_forecast(frame).sufficient_history
