"""Validation helpers for uploaded operations."""

from typing import Any

import pandas as pd


REQUIRED_COLUMNS = {"date", "amount", "operation_type", "description"}
ALLOWED_OPERATION_TYPES = {"income", "expense", "refund", "commission"}


def validate_required_columns(columns: list[str] | pd.Index) -> None:
    """Raise a readable error when required columns are absent."""

    missing = REQUIRED_COLUMNS.difference(str(column).strip().lower() for column in columns)
    if missing:
        raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(sorted(missing))}")


def validate_amount(value: Any) -> float:
    """Convert and validate a non-negative amount."""

    amount = float(value)
    if pd.isna(amount) or amount < 0:
        raise ValueError("Сумма операции должна быть неотрицательным числом")
    return amount


def validate_date(value: Any) -> pd.Timestamp:
    """Convert a value to a valid date."""

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Не удалось распознать дату: {value}")
    return parsed


def validate_operation_type(value: Any) -> str:
    """Validate operation type against the supported set."""

    operation_type = str(value).strip().lower()
    if operation_type not in ALLOWED_OPERATION_TYPES:
        raise ValueError(f"Недопустимый тип операции: {value}")
    return operation_type
