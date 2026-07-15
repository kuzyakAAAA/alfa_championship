"""Pure financial analytics functions."""

import pandas as pd

from schemas.analytics import AnalyticsMetrics, PeriodComparison


def _sum_for_types(frame: pd.DataFrame, operation_types: set[str]) -> float:
    return float(frame.loc[frame["operation_type"].isin(operation_types), "amount"].sum())


def calculate_revenue(frame: pd.DataFrame) -> float:
    return _sum_for_types(frame, {"income"})


def calculate_expenses(frame: pd.DataFrame) -> float:
    return _sum_for_types(frame, {"expense", "commission"})


def calculate_refunds(frame: pd.DataFrame) -> float:
    return _sum_for_types(frame, {"refund"})


def calculate_profit(frame: pd.DataFrame) -> float:
    return calculate_revenue(frame) - calculate_expenses(frame) - calculate_refunds(frame)


def calculate_sales_count(frame: pd.DataFrame) -> int:
    return int((frame["operation_type"] == "income").sum())


def calculate_average_check(frame: pd.DataFrame) -> float:
    count = calculate_sales_count(frame)
    return calculate_revenue(frame) / count if count else 0.0


def calculate_bank_fees(frame: pd.DataFrame) -> float:
    return _sum_for_types(frame, {"commission"})


def calculate_metrics(frame: pd.DataFrame) -> AnalyticsMetrics:
    """Calculate headline metrics for a normalized DataFrame."""

    return AnalyticsMetrics(
        revenue=calculate_revenue(frame),
        expenses=calculate_expenses(frame),
        profit=calculate_profit(frame),
        average_check=calculate_average_check(frame),
        sales_count=calculate_sales_count(frame),
        refunds=calculate_refunds(frame),
        bank_fees=calculate_bank_fees(frame),
    )


def group_expenses_by_category(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate expenses, commissions and refunds by category."""

    expenses = frame[frame["operation_type"].isin({"expense", "commission", "refund"})]
    return (
        expenses.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )


def revenue_by_month(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate income by calendar month."""

    income = frame[frame["operation_type"] == "income"].copy()
    if income.empty:
        return pd.DataFrame(columns=["month", "revenue"])
    income["month"] = pd.to_datetime(income["date"]).dt.to_period("M").dt.to_timestamp()
    return income.groupby("month", as_index=False)["amount"].sum().rename(columns={"amount": "revenue"})


def percent_change(current: float, previous: float) -> float | None:
    """Return percentage change, or no value for a zero baseline."""

    return None if previous == 0 else (current - previous) / abs(previous) * 100


def compare_periods(current: float, previous: float) -> PeriodComparison:
    return PeriodComparison(current, previous, percent_change(current, previous))


def compare_latest_months(frame: pd.DataFrame) -> dict[str, PeriodComparison]:
    """Compare revenue, expenses and profit in the two latest months."""

    data = frame.copy()
    data["month"] = pd.to_datetime(data["date"]).dt.to_period("M")
    months = sorted(data["month"].dropna().unique())
    if len(months) < 2:
        zero = PeriodComparison(0.0, 0.0, None)
        return {"revenue": zero, "expenses": zero, "profit": zero}
    previous_frame = data[data["month"] == months[-2]]
    current_frame = data[data["month"] == months[-1]]
    previous = calculate_metrics(previous_frame)
    current = calculate_metrics(current_frame)
    return {
        "revenue": compare_periods(current.revenue, previous.revenue),
        "expenses": compare_periods(current.expenses, previous.expenses),
        "profit": compare_periods(current.profit, previous.profit),
    }
