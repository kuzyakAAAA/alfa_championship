"""Tests for tariff cost and recommendation rules."""

import pandas as pd

from services.tariff_service import build_tariff_recommendation, calculate_tariff_cost


def tariff_frame() -> pd.DataFrame:
    return pd.DataFrame([
        {"name": "Старт", "monthly_fee": 0, "transfer_limit": 10, "transfer_commission": 50, "acquiring_commission": 0.02, "description": "Демо"},
        {"name": "Развитие", "monthly_fee": 500, "transfer_limit": 50, "transfer_commission": 20, "acquiring_commission": 0.01, "description": "Демо"},
    ])


def test_tariff_cost_includes_excess_and_acquiring() -> None:
    cost = calculate_tariff_cost(tariff_frame().iloc[0], 12, 10_000)
    assert cost.transfer_cost == 100
    assert cost.acquiring_cost == 200
    assert cost.total == 300


def test_recommendation_warns_near_limit() -> None:
    result = build_tariff_recommendation(tariff_frame(), "Старт", 9, 100_000, 12)
    assert result.recommended_tariff == "Развитие"
    assert result.savings > 0
    assert len(result.warnings) == 2
