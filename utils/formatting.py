"""Russian-friendly value formatting."""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import pandas as pd


def format_rubles(value: Any) -> str:
    """Format a value in rubles with grouped thousands and safe precision."""

    number = 0.0 if value is None or pd.isna(value) else float(value)
    amount = Decimal(str(number)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount == amount.to_integral():
        return f"{amount:,.0f} ₽".replace(",", " ")
    return f"{amount:,.2f} ₽".replace(",", " ").replace(".", ",")


def format_percent(value: Any, signed: bool = False) -> str:
    """Format a percentage value."""

    if value is None or pd.isna(value):
        return "нет данных"
    pattern = "+.1f" if signed else ".1f"
    return f"{float(value):{pattern}}%".replace(".", ",")


def format_date(value: date | datetime | pd.Timestamp | None) -> str:
    """Format a date or return a safe placeholder."""

    return "—" if value is None or pd.isna(value) else pd.Timestamp(value).strftime("%d.%m.%Y")


def format_large_number(value: Any) -> str:
    """Compactly format large values."""

    number = 0.0 if value is None or pd.isna(value) else float(value)
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.1f} млн"
    if abs(number) >= 1_000:
        return f"{number / 1_000:.1f} тыс."
    return f"{number:.0f}"
