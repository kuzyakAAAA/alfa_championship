"""Main dashboard page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analytics_service import calculate_metrics, compare_latest_months
from services.anomaly_service import detect_anomalies
from utils.formatting import format_percent, format_rubles
from utils.style import ALFA_RED, INK, frame_period, render_page_heading, style_plotly_figure


def render_page(frame: pd.DataFrame) -> None:
    """Render headline metrics and financial alerts."""

    render_page_heading("Главная", len(frame), frame_period(frame))
    metrics = calculate_metrics(frame)
    changes = compare_latest_months(frame)
    columns = st.columns(4)
    values = (
        ("Выручка", metrics.revenue, changes["revenue"].percent_change, "normal"),
        ("Расходы", metrics.expenses, changes["expenses"].percent_change, "inverse"),
        ("Прибыль", metrics.profit, changes["profit"].percent_change, "normal"),
        ("Средний чек", metrics.average_check, None, "off"),
    )
    for column, (label, value, delta, delta_color) in zip(columns, values, strict=False):
        column.metric(
            label,
            format_rubles(value),
            format_percent(delta, signed=True) if delta is not None else None,
            delta_color=delta_color,
        )

    monthly = frame.copy()
    monthly["Месяц"] = pd.to_datetime(monthly["date"]).dt.to_period("M").dt.to_timestamp()
    monthly["Поток"] = monthly["operation_type"].map(
        {"income": "Выручка", "expense": "Расходы", "commission": "Расходы", "refund": "Возвраты"}
    )
    chart = monthly.groupby(["Месяц", "Поток"], as_index=False)["amount"].sum()
    figure = px.line(
        chart,
        x="Месяц",
        y="amount",
        color="Поток",
        markers=True,
        labels={"amount": "Сумма, ₽"},
        color_discrete_map={"Выручка": ALFA_RED, "Расходы": INK, "Возвраты": "#9A9A9A"},
    )
    figure.update_traces(
        line={"width": 3},
        marker={"size": 7},
        hovertemplate="%{y:,.0f} ₽<extra>%{fullData.name}</extra>",
    )
    st.plotly_chart(style_plotly_figure(figure), width="stretch", theme=None)
    st.subheader("Финансовые сигналы")
    alerts = detect_anomalies(frame)
    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("Существенных отклонений по заданным правилам не обнаружено.")
