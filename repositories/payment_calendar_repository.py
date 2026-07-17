"""Persistence helpers for payment calendar settings and entries."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import CalendarProfile, PlannedCashflow
from schemas.payment_calendar import CalendarSettings, CashflowItem, CashflowItemInput
from services.payment_calendar_service import validate_cashflow_item, validate_settings


def get_or_create_profile(
    session: Session, profile_key: str, start_date: date
) -> CalendarProfile:
    profile = session.scalar(
        select(CalendarProfile).where(CalendarProfile.profile_key == profile_key)
    )
    if profile is None:
        profile = CalendarProfile(profile_key=profile_key, start_date=start_date)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def save_settings(session: Session, profile: CalendarProfile, settings: CalendarSettings) -> CalendarProfile:
    if settings.profile_key != profile.profile_key:
        raise ValueError("Нельзя сохранить настройки другого профиля.")
    validate_settings(settings)
    profile.balance_mode = settings.balance_mode
    profile.manual_balance = settings.manual_balance
    profile.start_date = settings.start_date
    profile.scenario = settings.scenario
    profile.horizon_days = settings.horizon_days
    session.commit()
    session.refresh(profile)
    return profile


def profile_to_settings(profile: CalendarProfile) -> CalendarSettings:
    return CalendarSettings(
        profile_key=profile.profile_key,
        start_date=profile.start_date,
        balance_mode=profile.balance_mode,
        manual_balance=float(profile.manual_balance) if profile.manual_balance is not None else None,
        scenario=profile.scenario,
        horizon_days=profile.horizon_days,
    )


def list_cashflows(session: Session, profile_id: int) -> list[CashflowItem]:
    statement = (
        select(PlannedCashflow)
        .where(PlannedCashflow.profile_id == profile_id)
        .order_by(PlannedCashflow.due_date, PlannedCashflow.id)
    )
    return [_to_schema(row) for row in session.scalars(statement)]


def create_cashflow(
    session: Session, profile_id: int, values: CashflowItemInput
) -> CashflowItem:
    profile = session.get(CalendarProfile, profile_id)
    if profile is None:
        raise ValueError("Профиль платёжного календаря не найден.")
    validate_cashflow_item(values, profile.start_date)
    row = PlannedCashflow(profile_id=profile_id, **_item_values(values))
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_schema(row)


def update_cashflow(
    session: Session, profile_id: int, item_id: int, values: CashflowItemInput
) -> CashflowItem | None:
    row = session.scalar(
        select(PlannedCashflow).where(
            PlannedCashflow.id == item_id,
            PlannedCashflow.profile_id == profile_id,
        )
    )
    if row is None:
        return None
    profile = session.get(CalendarProfile, profile_id)
    if profile is None:
        return None
    validate_cashflow_item(values, min(profile.start_date, row.due_date))
    for key, value in _item_values(values).items():
        setattr(row, key, value)
    session.commit()
    session.refresh(row)
    return _to_schema(row)


def delete_cashflow(session: Session, profile_id: int, item_id: int) -> bool:
    row = session.scalar(
        select(PlannedCashflow).where(
            PlannedCashflow.id == item_id,
            PlannedCashflow.profile_id == profile_id,
        )
    )
    if row is None:
        return False
    session.delete(row)
    session.commit()
    return True


def _item_values(values: CashflowItemInput) -> dict[str, object]:
    return {
        "kind": values.kind,
        "title": values.title,
        "amount": values.amount,
        "due_date": values.due_date,
        "category": values.category,
        "recurrence": values.recurrence,
        "recurrence_end": values.recurrence_end,
    }


def _to_schema(row: PlannedCashflow) -> CashflowItem:
    return CashflowItem(
        id=row.id,
        kind=row.kind,
        title=row.title,
        amount=float(row.amount),
        due_date=row.due_date,
        category=row.category,
        recurrence=row.recurrence,
        recurrence_end=row.recurrence_end,
    )
