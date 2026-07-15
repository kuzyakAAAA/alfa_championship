"""Detailed analytics page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analytics_service import calculate_metrics, group_expenses_by_category, revenue_by_month
from utils.formatting import format_rubles
from utils.style import ALFA_RED, frame_period, render_page_heading, style_plotly_figure


def render_page(frame: pd.DataFrame) -> None:
    """Render filters, charts and operation details."""

    render_page_heading("Аналитика", len(frame), frame_period(frame))
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    first, second = st.columns(2)
    date_range = first.date_input(
        "Период",
        (data["date"].min().date(), data["date"].max().date()),
        format="DD.MM.YYYY",
    )
    categories = second.multiselect("Категории", sorted(data["category"].unique()))
    operation_types = st.multiselect(
        "Типы операций", sorted(data["operation_type"].unique()), default=sorted(data["operation_type"].unique())
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        data = data[data["date"].dt.date.between(date_range[0], date_range[1])]
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
    revenue_figure = px.bar(
        revenue,
        x="month",
        y="revenue",
        labels={"month": "Месяц", "revenue": "Выручка, ₽"},
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
