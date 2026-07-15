"""Revenue forecast page."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.forecast_service import build_revenue_forecast, prepare_time_series
from utils.formatting import format_rubles


def render_page(frame: pd.DataFrame) -> None:
    """Render historical revenue and three forecast scenarios."""

    st.title("Прогноз")
    result = build_revenue_forecast(frame)
    if not result.sufficient_history:
        st.warning(result.message)
        return
    history = prepare_time_series(frame)
    figure = go.Figure()
    figure.add_scatter(x=history.index, y=history.values, name="История", mode="lines+markers")
    for scenario in result.scenarios:
        figure.add_scatter(x=[point.date for point in scenario.points], y=[point.value for point in scenario.points], name=scenario.name, mode="lines+markers")
    figure.update_layout(xaxis_title="Месяц", yaxis_title="Выручка, ₽", legend_title="Сценарий")
    st.plotly_chart(figure, width="stretch")
    base = next(item for item in result.scenarios if item.name == "Базовый")
    st.metric("Базовый прогноз на квартал", format_rubles(sum(point.value for point in base.points)))
    st.info(result.message)
    st.caption("Факторы сценариев: линейный тренд и отклонение ±15%. Прогноз не является финансовой гарантией.")
