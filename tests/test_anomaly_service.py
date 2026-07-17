"""Tests for historical alerts after cash-gap logic moved to the calendar."""

import pandas as pd

from services.anomaly_service import detect_anomalies


def test_historical_expense_excess_is_not_called_cash_gap() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-10", "2026-02-10", "2026-02-11"]),
            "operation_type": ["income", "income", "expense"],
            "amount": [1000, 100, 500],
        }
    )
    assert all("кассового разрыва" not in warning for warning in detect_anomalies(frame))
