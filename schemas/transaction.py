"""Transaction schemas."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TransactionInput:
    date: str
    amount: float
    operation_type: str
    description: str
    category: str | None = None
    payment_channel: str | None = None


@dataclass(frozen=True)
class CleanTransaction:
    operation_date: date
    amount: float
    operation_type: str
    category: str
    description: str
    payment_channel: str


@dataclass(frozen=True)
class CategorizationResult:
    category: str
    matched_keyword: str | None
