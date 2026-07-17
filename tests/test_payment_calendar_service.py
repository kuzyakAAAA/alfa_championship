"""Tests for deterministic payment-calendar calculations."""

from datetime import date

import pandas as pd
import pytest

from schemas.payment_calendar import CalendarSettings, CashflowItemInput
from services.payment_calendar_service import (
    build_payment_calendar,
    calculate_net_cashflow,
    expand_cashflow_items,
    validate_cashflow_item,
)


def history_frame() -> pd.DataFrame:
    rows = []
    for month, amount in enumerate([1000, 1100, 1200, 1300, 1400, 1500], start=1):
        rows.append({"date": f"2026-{month:02d}-05", "operation_type": "income", "amount": amount})
        rows.append({"date": f"2026-{month:02d}-15", "operation_type": "expense", "amount": 100})
    return pd.DataFrame(rows)


def settings(start: date, **changes: object) -> CalendarSettings:
    values = {
        "profile_key": "demo",
        "start_date": start,
        "balance_mode": "manual",
        "manual_balance": 1000.0,
        "scenario": "base",
        "horizon_days": 90,
    }
    values.update(changes)
    return CalendarSettings(**values)


def test_net_cashflow_counts_all_outflow_types() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2026-01-01"] * 4,
            "operation_type": ["income", "expense", "commission", "refund"],
            "amount": [1000, 200, 50, 100],
        }
    )
    assert calculate_net_cashflow(frame) == 650


def test_monthly_rule_clamps_day_to_end_of_short_month() -> None:
    item = CashflowItemInput(
        "payment", "Аренда", 100, date(2026, 1, 31), "Аренда", "monthly", date(2026, 3, 31)
    )
    dates = [
        value[0]
        for value in expand_cashflow_items(
            [item], start_date=date(2026, 1, 1), end_date=date(2026, 4, 30)
        )
    ]
    assert dates == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)]


def test_manual_receipt_replaces_same_amount_of_monthly_forecast() -> None:
    frame = history_frame()
    start = date(2026, 7, 1)
    baseline = build_payment_calendar(frame, settings(start), [])
    manual = CashflowItemInput("receipt", "Оплата договора", 500, date(2026, 7, 10))
    adjusted = build_payment_calendar(frame, settings(start), [manual])
    baseline_july = sum(point.forecast_receipts for point in baseline.points if point.date.month == 7)
    adjusted_july = sum(point.forecast_receipts for point in adjusted.points if point.date.month == 7)
    assert adjusted_july == pytest.approx(baseline_july - 500)
    adjusted_total_july = sum(
        point.forecast_receipts + point.manual_receipts
        for point in adjusted.points
        if point.date.month == 7
    )
    assert adjusted_total_july == pytest.approx(baseline_july)


def test_manual_receipt_cannot_make_automatic_forecast_negative() -> None:
    receipt = CashflowItemInput("receipt", "Крупный перевод", 100_000, date(2026, 7, 10))
    result = build_payment_calendar(history_frame(), settings(date(2026, 7, 1)), [receipt])
    assert sum(point.forecast_receipts for point in result.points if point.date.month == 7) == 0
    assert result.total_manual_receipts == 100_000


def test_current_month_actual_receipts_are_subtracted() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2026-01-05", "2026-02-05", "2026-03-05", "2026-04-05"],
            "operation_type": ["income"] * 4,
            "amount": [1000, 1000, 1000, 400],
        }
    )
    result = build_payment_calendar(
        frame, settings(date(2026, 4, 15), horizon_days=30), []
    )
    april_forecast = sum(
        point.forecast_receipts for point in result.points if point.date.month == 4
    )
    assert april_forecast == pytest.approx(600)


def test_insufficient_history_uses_only_manual_receipts() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2026-01-05", "2026-02-05"],
            "operation_type": ["income", "income"],
            "amount": [1000, 1000],
        }
    )
    receipt = CashflowItemInput("receipt", "Оплата", 300, date(2026, 3, 10))
    result = build_payment_calendar(
        frame, settings(date(2026, 3, 1), horizon_days=30), [receipt]
    )
    assert not result.sufficient_history
    assert result.total_forecast_receipts == 0
    assert result.total_receipts == 300


@pytest.mark.parametrize("horizon", [30, 60, 90])
def test_horizon_controls_number_of_daily_points(horizon: int) -> None:
    result = build_payment_calendar(
        history_frame(), settings(date(2026, 7, 1), horizon_days=horizon), []
    )
    assert len(result.points) == horizon


def test_first_negative_end_of_day_is_reported() -> None:
    payment = CashflowItemInput("payment", "Налог", 150, date(2026, 7, 1), "Налоги")
    result = build_payment_calendar(
        pd.DataFrame(columns=["date", "operation_type", "amount"]),
        settings(date(2026, 7, 1), manual_balance=100, horizon_days=30),
        [payment],
    )
    assert result.first_gap_date == date(2026, 7, 1)
    assert result.minimum_balance == -50
    assert result.maximum_shortage == 50


def test_scenarios_change_expected_receipts() -> None:
    pessimistic = build_payment_calendar(
        history_frame(), settings(date(2026, 7, 1), scenario="pessimistic"), []
    )
    optimistic = build_payment_calendar(
        history_frame(), settings(date(2026, 7, 1), scenario="optimistic"), []
    )
    assert pessimistic.total_forecast_receipts < optimistic.total_forecast_receipts


def test_invalid_payment_category_is_rejected() -> None:
    item = CashflowItemInput("payment", "Прочее", 100, date(2026, 7, 1), "Другое")
    with pytest.raises(ValueError, match="категорию"):
        validate_cashflow_item(item, date(2026, 7, 1))
