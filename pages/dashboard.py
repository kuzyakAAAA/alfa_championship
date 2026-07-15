"""Main dashboard page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analytics_service import calculate_metrics, compare_latest_months
from services.anomaly_service import detect_anomalies
from utils.formatting import format_percent, format_rubles


def render_page(frame: pd.DataFrame) -> None:
    """Render headline metrics and financial alerts."""

    st.title("Главная")
    metrics = calculate_metrics(frame)
    changes = compare_latest_months(frame)
    columns = st.columns(4)
    values = (
        ("Выручка", metrics.revenue, changes["revenue"].percent_change),
        ("Расходы", metrics.expenses, changes["expenses"].percent_change),
        ("Прибыль", metrics.profit, changes["profit"].percent_change),
        ("Средний чек", metrics.average_check, None),
    )
    for column, (label, value, delta) in zip(columns, values, strict=False):
        column.metric(label, format_rubles(value), format_percent(delta, signed=True) if delta is not None else None)

    monthly = frame.copy()
    monthly["Месяц"] = pd.to_datetime(monthly["date"]).dt.to_period("M").dt.to_timestamp()
    monthly["Поток"] = monthly["operation_type"].map(
        {"income": "Выручка", "expense": "Расходы", "commission": "Расходы", "refund": "Возвраты"}
    )
    chart = monthly.groupby(["Месяц", "Поток"], as_index=False)["amount"].sum()
    st.plotly_chart(px.line(chart, x="Месяц", y="amount", color="Поток", markers=True, labels={"amount": "Сумма, ₽"}), width="stretch")
    st.subheader("Финансовые сигналы")
    alerts = detect_anomalies(frame)
    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("Существенных отклонений по заданным правилам не обнаружено.")
