"""Validation helpers for uploaded operations."""

from datetime import date
from decimal import Decimal, InvalidOperation
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


def parse_russian_date_range(value: str) -> tuple[date, date]:
    """Parse a date range in the ``DD.MM.YYYY — DD.MM.YYYY`` format."""

    parts = [part.strip() for part in value.split("—")]
    if len(parts) != 2:
        raise ValueError("Укажите период через тире: 01.01.2001 — 31.12.2001")
    try:
        start = pd.to_datetime(parts[0], format="%d.%m.%Y").date()
        end = pd.to_datetime(parts[1], format="%d.%m.%Y").date()
    except (TypeError, ValueError) as error:
        raise ValueError("Используйте формат даты 01.01.2001") from error
    if start > end:
        raise ValueError("Дата начала периода не может быть позже даты окончания")
    return start, end


def parse_rubles(value: str) -> float:
    """Parse a ruble amount written with Russian separators and the ₽ sign."""

    normalized = value.replace("₽", "").replace(" ", "").replace("\u00a0", "").replace(",", ".").strip()
    try:
        amount = Decimal(normalized)
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Введите сумму в формате 710 700 ₽ или 710 700,50 ₽") from error
    if amount < 0:
        raise ValueError("Оборот не может быть отрицательным")
    return float(amount)
