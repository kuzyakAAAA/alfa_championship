"""Detailed analytics page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analytics_service import calculate_metrics, group_expenses_by_category, revenue_by_month
from utils.formatting import format_month, format_rubles
from utils.style import ALFA_RED, frame_period, render_page_heading, style_plotly_figure
from utils.validators import parse_russian_date_range


def render_page(frame: pd.DataFrame) -> None:
    """Render filters, charts and operation details."""

    render_page_heading("Аналитика", len(frame), frame_period(frame))
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    default_start = data["date"].min().date()
    default_end = data["date"].max().date()
    period_text = st.text_input(
        "Период",
        value=f"{default_start:%d.%m.%Y} — {default_end:%d.%m.%Y}",
        placeholder="01.01.2001 — 31.12.2001",
    )
    try:
        start_date, end_date = parse_russian_date_range(period_text)
    except ValueError as error:
        st.error(str(error))
        start_date, end_date = default_start, default_end
    data = data[data["date"].dt.date.between(start_date, end_date)]
    first, second = st.columns(2)
    categories = first.multiselect("Категории", sorted(data["category"].unique()))
    operation_types = second.multiselect(
        "Типы операций",
        sorted(data["operation_type"].unique()),
        default=sorted(data["operation_type"].unique()),
    )
    if categories:
        data = data[data["category"].isin(categories)]
    data = data[data["operation_type"].isin(operation_types)]
    metrics = calculate_metrics(data)
    stats = st.columns(4)
    stats[0].metric("Продажи", metrics.sales_count)
    stats[1].metric("Средний чек", format_rubles(metrics.average_check))
    stats[2].metric("Возвраты", format_rubles(metrics.refunds))
    stats[3].metric("Комиссии", format_rubles(metrics.bank_fees))
    left, right = st.columns(2)
    revenue = revenue_by_month(data)
    revenue["month_label"] = revenue["month"].map(format_month)
    revenue_figure = px.bar(
        revenue,
        x="month_label",
        y="revenue",
        labels={"month_label": "Месяц", "revenue": "Выручка, ₽"},
        color_discrete_sequence=[ALFA_RED],
    )
    revenue_figure.update_traces(marker_line_width=0, hovertemplate="%{y:,.0f} ₽<extra></extra>")
    left.plotly_chart(style_plotly_figure(revenue_figure), width="stretch", theme=None)
    expenses = group_expenses_by_category(data)
    expense_figure = px.pie(
        expenses,
        names="category",
        values="amount",
        hole=0.55,
        color_discrete_sequence=[ALFA_RED, "#111111", "#727272", "#F06B62", "#B9B9B9", "#F5A39D"],
    )
    expense_figure.update_traces(textposition="inside", textinfo="percent", marker={"line": {"color": "#FFFFFF", "width": 2}})
    right.plotly_chart(style_plotly_figure(expense_figure), width="stretch", theme=None)
    table = data.sort_values("date", ascending=False).copy()
    table["date"] = table["date"].dt.strftime("%d.%m.%Y")
    table["amount"] = table["amount"].map(format_rubles)
    table = table.rename(
        columns={
            "date": "Дата",
            "amount": "Сумма",
            "operation_type": "Тип операции",
            "category": "Категория",
            "description": "Описание",
            "payment_channel": "Канал оплаты",
        }
    )
    st.dataframe(table, width="stretch", hide_index=True)
