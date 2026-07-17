"""Payment calendar page with persisted settings and planned cashflows."""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy.orm import Session

from models import CalendarProfile
from repositories.payment_calendar_repository import (
    create_cashflow,
    delete_cashflow,
    save_settings,
    update_cashflow,
)
from schemas.payment_calendar import (
    PAYMENT_CATEGORIES,
    SCENARIO_LABELS,
    CalendarSettings,
    CashflowItem,
    CashflowItemInput,
    PaymentCalendarResult,
)
from services.payment_calendar_service import validate_cashflow_item, validate_settings
from utils.formatting import format_date, format_rubles
from utils.style import ALFA_RED, INK, frame_period, render_page_heading, style_plotly_figure


def render_page(
    frame: pd.DataFrame,
    session: Session,
    profile: CalendarProfile,
    settings: CalendarSettings,
    items: list[CashflowItem],
    result: PaymentCalendarResult,
) -> None:
    """Render settings, CRUD forms and the daily balance projection."""

    render_page_heading("Платёжный календарь", len(frame), frame_period(frame))
    _render_settings(session, profile, settings, result)
    _render_summary(result)
    _render_chart(result)
    _render_daily_table(result)
    _render_item_management(session, profile, settings, items)
    st.caption(
        "Прогноз основан на истории операций и введённых планах, не является гарантией "
        "поступлений и не проводит платежи автоматически."
    )


def _render_settings(
    session: Session,
    profile: CalendarProfile,
    settings: CalendarSettings,
    result: PaymentCalendarResult,
) -> None:
    with st.expander("Настройки прогноза", expanded=True):
        last_date = format_date(result.last_transaction_date)
        st.caption(
            f"Расчётный остаток по операциям до начала календаря: "
            f"{format_rubles(result.calculated_balance)}. Последняя операция в CSV: {last_date}."
        )
        with st.form(f"calendar_settings_{profile.profile_key}"):
            first, second = st.columns(2)
            balance_label = first.radio(
                "Стартовый остаток",
                ["Расчётный по CSV", "Фактический"],
                index=0 if settings.balance_mode == "calculated" else 1,
            )
            start_date = second.date_input("Начало календаря", value=settings.start_date)
            third, fourth, fifth = st.columns(3)
            manual_balance = third.number_input(
                "Фактический остаток, ₽",
                value=float(
                    settings.manual_balance
                    if settings.manual_balance is not None
                    else result.calculated_balance
                ),
                step=1000.0,
                help="Используется только в режиме «Фактический».",
            )
            scenario_options = list(SCENARIO_LABELS)
            scenario = fourth.selectbox(
                "Сценарий поступлений",
                scenario_options,
                index=scenario_options.index(settings.scenario),
                format_func=SCENARIO_LABELS.get,
            )
            horizon = fifth.selectbox(
                "Горизонт",
                [30, 60, 90],
                index=[30, 60, 90].index(settings.horizon_days),
                format_func=lambda value: f"{value} дней",
            )
            if st.form_submit_button("Сохранить настройки"):
                updated = CalendarSettings(
                    profile_key=settings.profile_key,
                    start_date=start_date,
                    balance_mode="calculated" if balance_label == "Расчётный по CSV" else "manual",
                    manual_balance=None if balance_label == "Расчётный по CSV" else float(manual_balance),
                    scenario=scenario,
                    horizon_days=horizon,
                )
                try:
                    validate_settings(updated)
                    save_settings(session, profile, updated)
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.success("Настройки сохранены.")
                    st.rerun()


def _render_summary(result: PaymentCalendarResult) -> None:
    metrics = st.columns(5)
    metrics[0].metric("Стартовый остаток", format_rubles(result.opening_balance))
    metrics[1].metric("Ожидается", format_rubles(result.total_receipts))
    metrics[2].metric("К оплате", format_rubles(result.total_payments))
    metrics[3].metric("Остаток в конце", format_rubles(result.ending_balance))
    metrics[4].metric("Минимальный остаток", format_rubles(result.minimum_balance))
    if result.first_gap_date:
        st.error(
            f"Прогнозируется кассовый разрыв {format_date(result.first_gap_date)}. "
            f"Максимальный дефицит — {format_rubles(result.maximum_shortage)}."
        )
    else:
        st.success(f"На горизонте {result.horizon_days} дней кассовый разрыв не прогнозируется.")
    if not result.sufficient_history:
        st.warning(result.message)
    else:
        st.caption(
            f"Автоматический прогноз: {format_rubles(result.total_forecast_receipts)} · "
            f"ручные поступления: {format_rubles(result.total_manual_receipts)}."
        )


def _render_chart(result: PaymentCalendarResult) -> None:
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    dates = [point.date for point in result.points]
    figure.add_trace(
        go.Bar(
            x=dates,
            y=[point.forecast_receipts + point.manual_receipts for point in result.points],
            name="Поступления",
            marker_color="#B9B9B9",
            hovertemplate="%{y:,.0f} ₽<extra>Поступления</extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Bar(
            x=dates,
            y=[-point.payments for point in result.points],
            name="Платежи",
            marker_color=ALFA_RED,
            hovertemplate="%{customdata:,.0f} ₽<extra>Платежи</extra>",
            customdata=[point.payments for point in result.points],
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=dates,
            y=[point.balance for point in result.points],
            name="Остаток",
            mode="lines",
            line={"color": INK, "width": 3},
            hovertemplate="%{y:,.0f} ₽<extra>Остаток</extra>",
        ),
        secondary_y=True,
    )
    figure.add_hline(y=0, line_dash="dot", line_color="#777777", secondary_y=True)
    figure.update_layout(barmode="relative")
    figure.update_yaxes(title_text="Поток, ₽", secondary_y=False)
    figure.update_yaxes(title_text="Остаток, ₽", secondary_y=True)
    st.plotly_chart(style_plotly_figure(figure), width="stretch", theme=None)


def _render_daily_table(result: PaymentCalendarResult) -> None:
    with st.expander("Прогноз по дням"):
        rows = []
        for point in result.points:
            rows.append(
                {
                    "Дата": format_date(point.date),
                    "Автопрогноз": format_rubles(point.forecast_receipts),
                    "Ручные поступления": format_rubles(point.manual_receipts),
                    "Платежи": format_rubles(point.payments),
                    "Чистый поток": format_rubles(point.net_flow),
                    "Остаток": format_rubles(point.balance),
                    "События": "; ".join((*point.receipt_titles, *point.payment_titles)) or "—",
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _render_item_management(
    session: Session,
    profile: CalendarProfile,
    settings: CalendarSettings,
    items: list[CashflowItem],
) -> None:
    st.subheader("Плановые операции")
    payment_tab, receipt_tab = st.tabs(["Добавить платёж", "Добавить поступление"])
    with payment_tab:
        _render_add_form(session, profile, settings, "payment")
    with receipt_tab:
        _render_add_form(session, profile, settings, "receipt")

    if not items:
        st.info("Плановых платежей и ручных поступлений пока нет.")
        return
    table = pd.DataFrame([_item_row(item) for item in items])
    st.dataframe(table, width="stretch", hide_index=True)
    _render_edit_form(session, profile, settings, items)


def _render_add_form(
    session: Session,
    profile: CalendarProfile,
    settings: CalendarSettings,
    kind: str,
) -> None:
    label = "платёж" if kind == "payment" else "поступление"
    with st.form(f"add_{kind}_{profile.profile_key}"):
        title = st.text_input("Название", placeholder="Например, аренда склада")
        first, second = st.columns(2)
        amount = first.number_input("Сумма, ₽", min_value=0.01, value=10_000.0, step=1000.0)
        due_date = second.date_input(
            "Первая дата", value=settings.start_date, min_value=settings.start_date
        )
        category = None
        if kind == "payment":
            category = st.selectbox("Категория", PAYMENT_CATEGORIES)
        recurrence = st.selectbox(
            "Повторение",
            ["once", "monthly"],
            format_func=lambda value: "Разово" if value == "once" else "Ежемесячно",
        )
        use_end = st.checkbox("Ограничить повторение датой")
        recurrence_end = st.date_input("Дата окончания", value=due_date)
        if st.form_submit_button(f"Добавить {label}"):
            values = CashflowItemInput(
                kind=kind,
                title=title.strip(),
                amount=float(amount),
                due_date=due_date,
                category=category,
                recurrence=recurrence,
                recurrence_end=recurrence_end if recurrence == "monthly" and use_end else None,
            )
            try:
                validate_cashflow_item(values, settings.start_date)
                create_cashflow(session, profile.id, values)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success(f"Запись «{values.title}» добавлена.")
                st.rerun()


def _render_edit_form(
    session: Session,
    profile: CalendarProfile,
    settings: CalendarSettings,
    items: list[CashflowItem],
) -> None:
    with st.expander("Изменить или удалить запись"):
        selected_id = st.selectbox(
            "Запись",
            [item.id for item in items],
            format_func=lambda item_id: next(
                f"{item.title} · {format_date(item.due_date)} · {format_rubles(item.amount)}"
                for item in items
                if item.id == item_id
            ),
        )
        selected = next(item for item in items if item.id == selected_id)
        with st.form(f"edit_cashflow_{profile.profile_key}_{selected.id}"):
            title = st.text_input("Название", value=selected.title)
            first, second = st.columns(2)
            amount = first.number_input(
                "Сумма, ₽", min_value=0.01, value=float(selected.amount), step=1000.0
            )
            due_date = second.date_input(
                "Первая дата",
                value=selected.due_date,
                min_value=min(settings.start_date, selected.due_date),
            )
            category = selected.category
            if selected.kind == "payment":
                category = st.selectbox(
                    "Категория",
                    PAYMENT_CATEGORIES,
                    index=PAYMENT_CATEGORIES.index(selected.category or PAYMENT_CATEGORIES[0]),
                )
            recurrence = st.selectbox(
                "Повторение",
                ["once", "monthly"],
                index=0 if selected.recurrence == "once" else 1,
                format_func=lambda value: "Разово" if value == "once" else "Ежемесячно",
            )
            use_end = st.checkbox(
                "Ограничить повторение датой", value=selected.recurrence_end is not None
            )
            recurrence_end = st.date_input(
                "Дата окончания",
                value=selected.recurrence_end or due_date,
            )
            save_button = st.form_submit_button("Сохранить")
            delete_button = st.form_submit_button("Удалить")
            if delete_button:
                delete_cashflow(session, profile.id, selected.id)
                st.success("Запись удалена.")
                st.rerun()
            if save_button:
                values = CashflowItemInput(
                    kind=selected.kind,
                    title=title.strip(),
                    amount=float(amount),
                    due_date=due_date,
                    category=category if selected.kind == "payment" else None,
                    recurrence=recurrence,
                    recurrence_end=recurrence_end if recurrence == "monthly" and use_end else None,
                )
                try:
                    validate_cashflow_item(values, min(settings.start_date, selected.due_date))
                    update_cashflow(session, profile.id, selected.id, values)
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.success("Запись обновлена.")
                    st.rerun()


def _item_row(item: CashflowItem) -> dict[str, str]:
    return {
        "ID": str(item.id),
        "Тип": "Платёж" if item.kind == "payment" else "Поступление",
        "Название": item.title,
        "Категория": item.category or "—",
        "Сумма": format_rubles(item.amount),
        "Первая дата": format_date(item.due_date),
        "Повторение": "Ежемесячно" if item.recurrence == "monthly" else "Разово",
        "Окончание": format_date(item.recurrence_end),
    }
