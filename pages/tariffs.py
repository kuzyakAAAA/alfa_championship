"""Tariff comparison page."""

import pandas as pd
import streamlit as st

from services.analytics_service import calculate_revenue
from services.tariff_service import build_tariff_recommendation, compare_tariffs
from utils.formatting import format_rubles
from utils.style import frame_period, render_page_heading


DISCLAIMER = "Все тарифы и финансовые условия в прототипе являются демонстрационными и не относятся к действующим продуктам Альфа-Банка."


def render_page(frame: pd.DataFrame, tariff_frame: pd.DataFrame) -> None:
    """Render tariff cost comparison and a transparent recommendation."""

    render_page_heading("Тарифы", len(frame), frame_period(frame))
    st.warning(DISCLAIMER)
    first, second = st.columns(2)
    current = first.selectbox("Текущий тариф", tariff_frame["name"].tolist())
    transfer_count = second.number_input("Переводов в месяц", min_value=0, value=int((frame["operation_type"] != "income").sum()))
    acquiring_turnover = st.number_input(
        "Оборот эквайринга, ₽",
        min_value=0.0,
        value=float(calculate_revenue(frame)),
        step=10_000.0,
        format="%.0f",
    )
    st.caption(format_rubles(acquiring_turnover))
    recommendation = build_tariff_recommendation(
        tariff_frame, current, int(transfer_count), float(acquiring_turnover), int(transfer_count * 1.15)
    )
    comparison = compare_tariffs(tariff_frame, int(transfer_count), float(acquiring_turnover))
    comparison = comparison.rename(columns={
        "tariff_name": "Тариф", "monthly_fee": "Абонентская плата", "transfer_cost": "Переводы",
        "acquiring_cost": "Эквайринг", "total": "Итого",
    })
    money_columns = ["Абонентская плата", "Переводы", "Эквайринг", "Итого"]
    comparison_view = comparison.style.format({column: format_rubles for column in money_columns})
    st.dataframe(comparison_view, width="stretch", hide_index=True)
    st.subheader(f"Рекомендация: {recommendation.recommended_tariff}")
    st.write(recommendation.reason)
    st.metric("Возможная экономия в месяц", format_rubles(recommendation.savings))
    for warning in recommendation.warnings:
        st.warning(warning)
    st.caption("Смена тарифа автоматически не выполняется.")
