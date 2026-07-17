"""Deterministic daily cash-balance forecast for the payment calendar."""

import calendar
from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from schemas.payment_calendar import (
    HORIZONS,
    PAYMENT_CATEGORIES,
    SCENARIO_FACTORS,
    CalendarSettings,
    CashflowItem,
    CashflowItemInput,
    DailyCashflowPoint,
    PaymentCalendarResult,
)


def validate_settings(settings: CalendarSettings) -> None:
    """Reject unsupported persisted values before calculating a calendar."""

    if settings.profile_key not in {"demo", "uploaded"}:
        raise ValueError("Неизвестный профиль платёжного календаря.")
    if settings.balance_mode not in {"calculated", "manual"}:
        raise ValueError("Неизвестный режим стартового остатка.")
    if settings.balance_mode == "manual" and settings.manual_balance is None:
        raise ValueError("Укажите фактический стартовый остаток.")
    if settings.manual_balance is not None and not np.isfinite(settings.manual_balance):
        raise ValueError("Стартовый остаток должен быть числом.")
    if settings.scenario not in SCENARIO_FACTORS:
        raise ValueError("Неизвестный сценарий прогноза.")
    if settings.horizon_days not in HORIZONS:
        raise ValueError("Горизонт должен составлять 30, 60 или 90 дней.")


def validate_cashflow_item(values: CashflowItemInput, start_date: date) -> None:
    """Validate a manually entered payment or receipt."""

    if values.kind not in {"payment", "receipt"}:
        raise ValueError("Неизвестный тип записи.")
    if not values.title.strip():
        raise ValueError("Укажите название платежа или поступления.")
    if len(values.title.strip()) > 200:
        raise ValueError("Название не должно превышать 200 символов.")
    if not np.isfinite(values.amount) or values.amount <= 0:
        raise ValueError("Сумма должна быть больше нуля.")
    if values.due_date < start_date:
        raise ValueError("Дата не может быть раньше начала календаря.")
    if values.kind == "payment" and values.category not in PAYMENT_CATEGORIES:
        raise ValueError("Выберите допустимую категорию платежа.")
    if values.kind == "receipt" and values.category is not None:
        raise ValueError("Для поступления категория платежа не задаётся.")
    if values.recurrence not in {"once", "monthly"}:
        raise ValueError("Поддерживаются разовые и ежемесячные записи.")
    if values.recurrence_end is not None:
        if values.recurrence != "monthly":
            raise ValueError("Дата окончания доступна только для ежемесячной записи.")
        if values.recurrence_end < values.due_date:
            raise ValueError("Дата окончания не может быть раньше первой даты.")


def calculate_net_cashflow(frame: pd.DataFrame, before: date | None = None) -> float:
    """Calculate the balance change represented by normalized transactions."""

    if frame.empty:
        return 0.0
    data = frame.copy()
    if before is not None:
        dates = pd.to_datetime(data["date"]).dt.date
        data = data[dates < before]
    income = data.loc[data["operation_type"] == "income", "amount"].sum()
    outflow = data.loc[
        data["operation_type"].isin({"expense", "commission", "refund"}), "amount"
    ].sum()
    return float(income - outflow)


def expand_cashflow_items(
    items: Iterable[CashflowItem | CashflowItemInput], start_date: date, end_date: date
) -> list[tuple[date, CashflowItem | CashflowItemInput]]:
    """Expand one-time and monthly rules into dated occurrences."""

    occurrences: list[tuple[date, CashflowItem | CashflowItemInput]] = []
    for item in items:
        if item.recurrence == "once":
            if start_date <= item.due_date <= end_date:
                occurrences.append((item.due_date, item))
            continue
        year, month = item.due_date.year, item.due_date.month
        while True:
            day = min(item.due_date.day, calendar.monthrange(year, month)[1])
            occurrence_date = date(year, month, day)
            if occurrence_date > end_date:
                break
            if item.recurrence_end is not None and occurrence_date > item.recurrence_end:
                break
            if occurrence_date >= item.due_date and occurrence_date >= start_date:
                occurrences.append((occurrence_date, item))
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1
    return sorted(occurrences, key=lambda value: (value[0], value[1].title))


def build_payment_calendar(
    frame: pd.DataFrame,
    settings: CalendarSettings,
    items: Iterable[CashflowItem | CashflowItemInput],
    today: date | None = None,
) -> PaymentCalendarResult:
    """Build a daily balance projection from history and planned cashflows."""

    del today  # The explicit persisted start date makes tests and saved views reproducible.
    validate_settings(settings)
    item_list = list(items)
    for item in item_list:
        # Old recurring rules may start before a newly selected calendar date.
        validation_start = min(settings.start_date, item.due_date)
        validate_cashflow_item(item, validation_start)

    start_date = settings.start_date
    end_date = start_date + timedelta(days=settings.horizon_days - 1)
    calculated_balance = calculate_net_cashflow(frame, before=start_date)
    opening_balance = (
        float(settings.manual_balance or 0.0)
        if settings.balance_mode == "manual"
        else calculated_balance
    )
    last_transaction_date = _last_transaction_date(frame)

    occurrences = expand_cashflow_items(item_list, start_date, end_date)
    payments: dict[date, float] = defaultdict(float)
    manual_receipts: dict[date, float] = defaultdict(float)
    payment_titles: dict[date, list[str]] = defaultdict(list)
    receipt_titles: dict[date, list[str]] = defaultdict(list)
    for occurrence_date, item in occurrences:
        if item.kind == "payment":
            payments[occurrence_date] += float(item.amount)
            payment_titles[occurrence_date].append(item.title)
        else:
            manual_receipts[occurrence_date] += float(item.amount)
            receipt_titles[occurrence_date].append(item.title)

    forecast_month_end = pd.Timestamp(end_date).to_period("M").end_time.date()
    forecast_manual_receipts: dict[date, float] = defaultdict(float)
    for occurrence_date, item in expand_cashflow_items(
        item_list, start_date, forecast_month_end
    ):
        if item.kind == "receipt":
            forecast_manual_receipts[occurrence_date] += float(item.amount)

    forecast_receipts, sufficient_history = _forecast_daily_receipts(
        frame,
        start_date,
        end_date,
        settings.scenario,
        forecast_manual_receipts,
    )
    points: list[DailyCashflowPoint] = []
    balance = opening_balance
    current_date = start_date
    while current_date <= end_date:
        predicted = forecast_receipts.get(current_date, 0.0)
        manual = manual_receipts.get(current_date, 0.0)
        outflow = payments.get(current_date, 0.0)
        net_flow = predicted + manual - outflow
        balance += net_flow
        points.append(
            DailyCashflowPoint(
                date=current_date,
                forecast_receipts=predicted,
                manual_receipts=manual,
                payments=outflow,
                net_flow=net_flow,
                balance=balance,
                payment_titles=tuple(payment_titles.get(current_date, ())),
                receipt_titles=tuple(receipt_titles.get(current_date, ())),
            )
        )
        current_date += timedelta(days=1)

    first_gap = next((point.date for point in points if point.balance < 0), None)
    minimum_balance = min((point.balance for point in points), default=opening_balance)
    total_forecast = sum(point.forecast_receipts for point in points)
    total_manual = sum(point.manual_receipts for point in points)
    total_payments = sum(point.payments for point in points)
    message = (
        "Автоматический прогноз рассчитан по полным месяцам истории."
        if sufficient_history
        else "Для автоматического прогноза нужны минимум три полных месяца; учтены только ручные поступления."
    )
    return PaymentCalendarResult(
        points=points,
        opening_balance=opening_balance,
        calculated_balance=calculated_balance,
        total_forecast_receipts=total_forecast,
        total_manual_receipts=total_manual,
        total_receipts=total_forecast + total_manual,
        total_payments=total_payments,
        ending_balance=points[-1].balance if points else opening_balance,
        minimum_balance=minimum_balance,
        first_gap_date=first_gap,
        maximum_shortage=max(0.0, -minimum_balance),
        sufficient_history=sufficient_history,
        message=message,
        horizon_days=settings.horizon_days,
        scenario=settings.scenario,
        last_transaction_date=last_transaction_date,
    )


def _forecast_daily_receipts(
    frame: pd.DataFrame,
    start_date: date,
    end_date: date,
    scenario: str,
    manual_receipts: dict[date, float],
) -> tuple[dict[date, float], bool]:
    if frame.empty:
        return {}, False
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    income = data[data["operation_type"] == "income"].copy()
    if income.empty:
        return {}, False

    start_month = pd.Timestamp(start_date).to_period("M")
    income["month"] = income["date"].dt.to_period("M")
    first_month = income["month"].min()
    full_month_index = pd.period_range(first_month, start_month - 1, freq="M")
    monthly = income.groupby("month")["amount"].sum().reindex(full_month_index, fill_value=0.0)
    if len(monthly) < 3:
        return {}, False

    x = np.array([period.ordinal for period in monthly.index], dtype=float).reshape(-1, 1)
    model = LinearRegression().fit(x, monthly.to_numpy(dtype=float))
    weekdays = _weekday_income_profile(income, start_date)
    target_months = pd.period_range(start_month, pd.Timestamp(end_date).to_period("M"), freq="M")
    result: dict[date, float] = {}
    for target_month in target_months:
        predicted_total = max(
            float(model.predict(np.array([[target_month.ordinal]], dtype=float))[0])
            * SCENARIO_FACTORS[scenario],
            0.0,
        )
        month_start = target_month.start_time.date()
        month_end = target_month.end_time.date()
        range_start = max(start_date, month_start)
        # Distribute a monthly total across the full remaining month and only
        # take the days that fall inside the selected rolling horizon later.
        range_end = month_end
        actual_before_start = float(
            income.loc[
                (income["month"] == target_month)
                & (income["date"].dt.date < start_date),
                "amount",
            ].sum()
        )
        known_manual = sum(
            amount
            for receipt_date, amount in manual_receipts.items()
            if receipt_date.year == target_month.year and receipt_date.month == target_month.month
        )
        remainder = max(predicted_total - actual_before_start - known_manual, 0.0)
        dates = list(pd.date_range(range_start, range_end, freq="D"))
        weights = [weekdays.get(point.weekday(), 0.0) for point in dates]
        weight_sum = sum(weights)
        if weight_sum <= 0:
            weights = [1.0] * len(dates)
            weight_sum = float(len(dates))
        for point, weight in zip(dates, weights, strict=False):
            result[point.date()] = remainder * weight / weight_sum
    return result, True


def _weekday_income_profile(income: pd.DataFrame, start_date: date) -> dict[int, float]:
    historical = income[income["date"].dt.date < start_date]
    if historical.empty:
        return {}
    start = historical["date"].min().normalize()
    cutoff = pd.Timestamp(start_date - timedelta(days=1))
    end = min(historical["date"].max().normalize(), cutoff)
    daily = historical.set_index("date")["amount"].resample("D").sum()
    daily = daily.reindex(pd.date_range(start, end, freq="D"), fill_value=0.0)
    return daily.groupby(daily.index.weekday).mean().astype(float).to_dict()


def _last_transaction_date(frame: pd.DataFrame) -> date | None:
    if frame.empty:
        return None
    value = pd.to_datetime(frame["date"], errors="coerce").max()
    return None if pd.isna(value) else value.date()
