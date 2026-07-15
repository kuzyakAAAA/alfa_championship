"""Tariff comparison page."""

import pandas as pd
import streamlit as st

from services.analytics_service import calculate_revenue
from services.tariff_service import build_tariff_recommendation, compare_tariffs
from utils.formatting import format_rubles
from utils.style import frame_period, render_page_heading
from utils.validators import parse_rubles


DISCLAIMER = "Все тарифы и финансовые условия в прототипе являются демонстрационными и не относятся к действующим продуктам Альфа-Банка."


def render_page(frame: pd.DataFrame, tariff_frame: pd.DataFrame) -> None:
    """Render tariff cost comparison and a transparent recommendation."""

    render_page_heading("Тарифы", len(frame), frame_period(frame))
    st.warning(DISCLAIMER)
    first, second = st.columns(2)
    current = first.selectbox("Текущий тариф", tariff_frame["name"].tolist())
    transfer_count = second.number_input("Переводов в месяц", min_value=0, value=int((frame["operation_type"] != "income").sum()))
    default_turnover = float(calculate_revenue(frame))
    turnover_text = st.text_input(
        "Оборот эквайринга, ₽",
        value=format_rubles(default_turnover),
    )
    try:
        acquiring_turnover = parse_rubles(turnover_text)
    except ValueError as error:
        st.error(str(error))
        acquiring_turnover = default_turnover
    recommendation = build_tariff_recommendation(
        tariff_frame, current, int(transfer_count), float(acquiring_turnover), int(transfer_count * 1.15)
    )
    comparison = compare_tariffs(tariff_frame, int(transfer_count), float(acquiring_turnover))
    comparison = comparison.rename(columns={
        "tariff_name": "Тариф", "monthly_fee": "Абонентская плата", "transfer_cost": "Переводы",
        "acquiring_cost": "Эквайринг", "total": "Итого",
    })
    money_columns = ["Абонентская плата", "Переводы", "Эквайринг", "Итого"]
    comparison_view = comparison.copy()
    for column in money_columns:
        comparison_view[column] = comparison_view[column].map(format_rubles)
    st.dataframe(comparison_view, width="stretch", hide_index=True)
    st.subheader(f"Рекомендация: {recommendation.recommended_tariff}")
    st.write(recommendation.reason)
    st.metric("Возможная экономия в месяц", format_rubles(recommendation.savings))
    for warning in recommendation.warnings:
        st.warning(warning)
    st.caption("Смена тарифа автоматически не выполняется.")
