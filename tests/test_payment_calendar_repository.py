"""Repository tests using isolated in-memory SQLite."""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from repositories.payment_calendar_repository import (
    create_cashflow,
    delete_cashflow,
    get_or_create_profile,
    list_cashflows,
    profile_to_settings,
    save_settings,
    update_cashflow,
)
from schemas.payment_calendar import CalendarSettings, CashflowItemInput


def test_profiles_and_cashflows_persist_and_are_isolated() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        demo = get_or_create_profile(session, "demo", date(2026, 7, 1))
        uploaded = get_or_create_profile(session, "uploaded", date(2026, 7, 2))
        created = create_cashflow(
            session,
            demo.id,
            CashflowItemInput("payment", "Аренда", 5000, date(2026, 7, 10), "Аренда"),
        )
        assert list_cashflows(session, uploaded.id) == []
        assert [item.title for item in list_cashflows(session, demo.id)] == ["Аренда"]

    with Session(engine) as session:
        demo = get_or_create_profile(session, "demo", date(2030, 1, 1))
        assert profile_to_settings(demo).start_date == date(2026, 7, 1)
        updated = update_cashflow(
            session,
            demo.id,
            created.id,
            CashflowItemInput("payment", "Новая аренда", 6000, date(2026, 7, 11), "Аренда"),
        )
        assert updated is not None and updated.amount == 6000
        assert delete_cashflow(session, demo.id, created.id)
        assert list_cashflows(session, demo.id) == []


def test_settings_are_saved() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        profile = get_or_create_profile(session, "demo", date(2026, 7, 1))
        values = CalendarSettings(
            "demo", date(2026, 7, 5), "manual", 1234.5, "optimistic", 30
        )
        save_settings(session, profile, values)
        assert profile_to_settings(profile) == values


def test_repository_rejects_invalid_item() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        profile = get_or_create_profile(session, "demo", date(2026, 7, 1))
        invalid = CashflowItemInput(
            "payment", "Налог", 0, date(2026, 7, 10), "Налоги"
        )
        with pytest.raises(ValueError, match="больше нуля"):
            create_cashflow(session, profile.id, invalid)
