"""Tariff comparison page."""

import pandas as pd
import streamlit as st

from services.analytics_service import calculate_revenue
from services.tariff_service import build_tariff_recommendation, compare_tariffs
from utils.formatting import format_rubles


DISCLAIMER = "Все тарифы и финансовые условия в прототипе являются демонстрационными и не относятся к действующим продуктам Альфа-Банка."


def render_page(frame: pd.DataFrame, tariff_frame: pd.DataFrame) -> None:
    """Render tariff cost comparison and a transparent recommendation."""

    st.title("Тарифы")
    st.warning(DISCLAIMER)
    current = st.selectbox("Текущий тариф", tariff_frame["name"].tolist())
    transfer_count = st.number_input("Количество переводов в месяц", min_value=0, value=int((frame["operation_type"] != "income").sum()))
    acquiring_turnover = st.number_input("Оборот эквайринга, ₽", min_value=0.0, value=float(calculate_revenue(frame)), step=10_000.0)
    recommendation = build_tariff_recommendation(
        tariff_frame, current, int(transfer_count), float(acquiring_turnover), int(transfer_count * 1.15)
    )
    comparison = compare_tariffs(tariff_frame, int(transfer_count), float(acquiring_turnover))
    comparison = comparison.rename(columns={
        "tariff_name": "Тариф", "monthly_fee": "Абонентская плата", "transfer_cost": "Переводы",
        "acquiring_cost": "Эквайринг", "total": "Итого",
    })
    st.dataframe(comparison, width="stretch", hide_index=True)
    st.subheader(f"Рекомендация: {recommendation.recommended_tariff}")
    st.write(recommendation.reason)
    st.metric("Возможная экономия в месяц", format_rubles(recommendation.savings))
    for warning in recommendation.warnings:
        st.warning(warning)
    st.caption("Смена тарифа автоматически не выполняется.")
