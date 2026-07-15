"""Tests for user-facing financial and date formatting."""

from datetime import date

from utils.formatting import format_date, format_rubles


def test_format_rubles_groups_thousands() -> None:
    assert format_rubles(1_234_567) == "1 234 567 ₽"


def test_format_rubles_keeps_fractional_part() -> None:
    assert format_rubles(12_081.9) == "12 081,90 ₽"


def test_format_date_uses_day_month_year() -> None:
    assert format_date(date(2001, 1, 1)) == "01.01.2001"
