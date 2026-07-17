"""Rule-based financial anomaly detection."""

import pandas as pd

from services.analytics_service import calculate_expenses, calculate_revenue


def detect_anomalies(frame: pd.DataFrame) -> list[str]:
    """Return readable warnings based on monthly and transaction-level rules."""

    if frame.empty:
        return []
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["month"] = data["date"].dt.to_period("M")
    warnings: list[str] = []
    expense_rows = data[data["operation_type"].isin({"expense", "commission"})]
    if not expense_rows.empty:
        threshold = expense_rows["amount"].mean() + 2 * expense_rows["amount"].std(ddof=0)
        if (expense_rows["amount"] > threshold).any():
            warnings.append("Обнаружена необычно крупная расходная операция.")
    months = sorted(data["month"].unique())
    if len(months) >= 2:
        previous = data[data["month"] == months[-2]]
        current = data[data["month"] == months[-1]]
        previous_revenue, current_revenue = calculate_revenue(previous), calculate_revenue(current)
        previous_expenses, current_expenses = calculate_expenses(previous), calculate_expenses(current)
        if previous_expenses and current_expenses > previous_expenses * 1.3:
            warnings.append("Расходы за последний месяц выросли более чем на 30%.")
        if previous_revenue and current_revenue < previous_revenue * 0.85:
            warnings.append("Выручка за последний месяц снизилась более чем на 15%.")
        for operation_type, label in (("refund", "Возвраты"), ("commission", "Банковские комиссии")):
            old = previous.loc[previous["operation_type"] == operation_type, "amount"].sum()
            new = current.loc[current["operation_type"] == operation_type, "amount"].sum()
            if old and new > old * 1.3:
                warnings.append(f"{label} заметно выросли относительно прошлого месяца.")
    return warnings
