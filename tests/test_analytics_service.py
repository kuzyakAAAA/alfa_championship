"""Tests for pure analytics calculations."""

import pandas as pd

from services.analytics_service import calculate_metrics, percent_change


def test_calculate_metrics() -> None:
    frame = pd.DataFrame({
        "operation_type": ["income", "income", "expense", "refund", "commission"],
        "amount": [1000.0, 500.0, 400.0, 100.0, 20.0],
    })
    metrics = calculate_metrics(frame)
    assert metrics.revenue == 1500.0
    assert metrics.expenses == 420.0
    assert metrics.profit == 980.0
    assert metrics.average_check == 750.0
    assert metrics.sales_count == 2
    assert metrics.refunds == 100.0
    assert metrics.bank_fees == 20.0


def test_percent_change_handles_zero_baseline() -> None:
    assert percent_change(100.0, 0.0) is None
    assert percent_change(120.0, 100.0) == 20.0
