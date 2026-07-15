"""Tests for user-facing financial and date formatting."""

from datetime import date

from utils.formatting import format_date, format_month, format_rubles
from utils.validators import parse_russian_date_range, parse_rubles


def test_format_rubles_groups_thousands() -> None:
    assert format_rubles(1_234_567) == "1 234 567 ₽"


def test_format_rubles_keeps_fractional_part() -> None:
    assert format_rubles(12_081.9) == "12 081,90 ₽"


def test_format_date_uses_day_month_year() -> None:
    assert format_date(date(2001, 1, 1)) == "01.01.2001"


def test_parse_russian_date_range() -> None:
    assert parse_russian_date_range("01.01.2001 — 31.12.2001") == (
        date(2001, 1, 1),
        date(2001, 12, 31),
    )


def test_format_month_uses_russian_name() -> None:
    assert format_month(date(2001, 3, 1)) == "Март"


def test_parse_rubles_accepts_grouped_amount() -> None:
    assert parse_rubles("710 700,50 ₽") == 710_700.5
