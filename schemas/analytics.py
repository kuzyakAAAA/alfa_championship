"""Analytics result schemas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsMetrics:
    revenue: float
    expenses: float
    profit: float
    average_check: float
    sales_count: int
    refunds: float
    bank_fees: float


@dataclass(frozen=True)
class PeriodComparison:
    current: float
    previous: float
    percent_change: float | None


@dataclass(frozen=True)
class ExpenseByCategory:
    category: str
    amount: float
