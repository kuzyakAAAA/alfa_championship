"""Data structures used by the payment calendar."""

from dataclasses import dataclass, field
from datetime import date


PAYMENT_CATEGORIES = (
    "Аренда",
    "Налоги",
    "Зарплата",
    "Поставщики",
    "Кредиты",
    "Подписки",
    "Реклама",
)
SCENARIO_FACTORS = {"pessimistic": 0.85, "base": 1.0, "optimistic": 1.15}
SCENARIO_LABELS = {
    "pessimistic": "Пессимистичный",
    "base": "Базовый",
    "optimistic": "Оптимистичный",
}
HORIZONS = (30, 60, 90)


@dataclass(frozen=True)
class CashflowItemInput:
    kind: str
    title: str
    amount: float
    due_date: date
    category: str | None = None
    recurrence: str = "once"
    recurrence_end: date | None = None


@dataclass(frozen=True)
class CashflowItem(CashflowItemInput):
    id: int = 0


@dataclass(frozen=True)
class CalendarSettings:
    profile_key: str
    start_date: date
    balance_mode: str = "calculated"
    manual_balance: float | None = None
    scenario: str = "base"
    horizon_days: int = 90


@dataclass(frozen=True)
class DailyCashflowPoint:
    date: date
    forecast_receipts: float
    manual_receipts: float
    payments: float
    net_flow: float
    balance: float
    payment_titles: tuple[str, ...] = field(default_factory=tuple)
    receipt_titles: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PaymentCalendarResult:
    points: list[DailyCashflowPoint]
    opening_balance: float
    calculated_balance: float
    total_forecast_receipts: float
    total_manual_receipts: float
    total_receipts: float
    total_payments: float
    ending_balance: float
    minimum_balance: float
    first_gap_date: date | None
    maximum_shortage: float
    sufficient_history: bool
    message: str
    horizon_days: int
    scenario: str
    last_transaction_date: date | None
