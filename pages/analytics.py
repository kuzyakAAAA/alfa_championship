"""Detailed analytics page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analytics_service import calculate_metrics, group_expenses_by_category, revenue_by_month
from utils.formatting import format_rubles


def render_page(frame: pd.DataFrame) -> None:
    """Render filters, charts and operation details."""

    st.title("Аналитика")
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    first, second = st.columns(2)
    date_range = first.date_input("Период", (data["date"].min().date(), data["date"].max().date()))
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
    left.plotly_chart(px.bar(revenue, x="month", y="revenue", labels={"month": "Месяц", "revenue": "Выручка, ₽"}), width="stretch")
    expenses = group_expenses_by_category(data)
    right.plotly_chart(px.pie(expenses, names="category", values="amount", hole=0.45), width="stretch")
    st.dataframe(data.sort_values("date", ascending=False), width="stretch", hide_index=True)
