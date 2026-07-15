"""Financial assistant chat page."""

from dataclasses import asdict

import pandas as pd
import streamlit as st

from config import (
    GIGACHAT_CA_BUNDLE_FILE,
    GIGACHAT_CREDENTIALS,
    GIGACHAT_MAX_TOKENS,
    GIGACHAT_MODEL,
    GIGACHAT_SCOPE,
    GIGACHAT_TEMPERATURE,
    GIGACHAT_TIMEOUT,
    GIGACHAT_VERIFY_SSL_CERTS,
)
from services.ai_service import answer_question, prepare_ai_context
from services.ai_service import AIServiceError, GigaChatAIService
from services.analytics_service import calculate_metrics, calculate_revenue
from services.anomaly_service import detect_anomalies
from services.forecast_service import build_revenue_forecast
from services.tariff_service import build_tariff_recommendation
from utils.style import frame_period, render_page_heading


EXAMPLES = [
    "Какая у меня прибыль?",
    "Что происходит с расходами?",
    "Какие финансовые риски обнаружены?",
]


def render_page(frame: pd.DataFrame) -> None:
    """Render a session-based context-bound chat."""

    render_page_heading("ИИ-помощник", len(frame), frame_period(frame))
    if not GIGACHAT_CREDENTIALS:
        st.info("API-ключ не задан: помощник работает в безопасном mock-режиме.")
    st.caption("Примеры: " + " · ".join(EXAMPLES))
    history = st.session_state.setdefault("chat_history", [])
    for message in history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    question = st.chat_input("Спросите о рассчитанных показателях")
    if question:
        context = prepare_ai_context(calculate_metrics(frame), detect_anomalies(frame))
        answer = answer_question(question, context, GIGACHAT_CREDENTIALS or "")
        history.extend(({"role": "user", "content": question}, {"role": "assistant", "content": answer}))
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.write(answer)


FULL_EXAMPLES = [
    "Почему снизилась прибыль?",
    "Какие расходы выросли сильнее всего?",
    "Какая выручка ожидается в следующем квартале?",
    "Какой тариф сейчас выгоднее?",
    "Есть ли риск кассового разрыва?",
    "На какие показатели стоит обратить внимание?",
]


def _build_context(
    service: GigaChatAIService, frame: pd.DataFrame, tariff_frame: pd.DataFrame
) -> str:
    """Create an anonymized aggregate context from existing calculation services."""

    metrics = asdict(calculate_metrics(frame))
    metrics["period"] = frame_period(frame)
    alerts = [
        {"severity": "warning", "title": "Финансовый сигнал", "description": message}
        for message in detect_anomalies(frame)
    ]
    forecast_result = build_revenue_forecast(frame)
    forecast: dict[str, object] | None = None
    if forecast_result.sufficient_history:
        totals = {
            scenario.name: sum(point.value for point in scenario.points)
            for scenario in forecast_result.scenarios
        }
        forecast = {
            "period": "Следующие 3 месяца",
            "pessimistic": totals.get("Пессимистичный"),
            "base": totals.get("Базовый"),
            "optimistic": totals.get("Оптимистичный"),
            "is_guaranteed": False,
            "message": forecast_result.message,
        }
    tariff_context: dict[str, object] | None = None
    if not tariff_frame.empty:
        transfer_count = int((frame["operation_type"] != "income").sum())
        recommendation = build_tariff_recommendation(
            tariff_frame,
            str(tariff_frame.iloc[0]["name"]),
            transfer_count,
            calculate_revenue(frame),
            int(transfer_count * 1.15),
        )
        tariff_context = {
            "current_tariff": recommendation.current_tariff,
            "recommended_tariff": recommendation.recommended_tariff,
            "change_recommended_now": False,
            "expected_monthly_savings": recommendation.savings,
            "reason": recommendation.reason,
        }
    return service.build_financial_context(metrics, alerts, forecast, tariff_context)


def render_page(frame: pd.DataFrame, tariff_frame: pd.DataFrame) -> None:
    """Render a GigaChat conversation with a safe mock-mode fallback."""

    render_page_heading("ИИ-помощник", len(frame), frame_period(frame))
    st.write("Помощник объясняет только показатели, которые уже рассчитало приложение.")
    service = GigaChatAIService(
        credentials=GIGACHAT_CREDENTIALS,
        scope=GIGACHAT_SCOPE,
        model=GIGACHAT_MODEL,
        max_tokens=GIGACHAT_MAX_TOKENS,
        temperature=GIGACHAT_TEMPERATURE,
        timeout=GIGACHAT_TIMEOUT,
        verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS,
        ca_bundle_file=GIGACHAT_CA_BUNDLE_FILE,
    )
    st.session_state["financial_context"] = _build_context(service, frame, tariff_frame)
    if service.is_configured():
        st.success("GigaChat API подключён")
    else:
        st.info("Демонстрационный режим: GigaChat API не подключён")
    if not GIGACHAT_VERIFY_SSL_CERTS:
        st.warning("Внимание: проверка SSL-сертификатов отключена")
    st.warning(
        "Исходные операции и персональные данные не отправляются. Ответы не заменяют "
        "бухгалтерскую, налоговую или юридическую консультацию."
    )
    clear_col, examples_col = st.columns([1, 4])
    if clear_col.button("Очистить историю", icon=":material/delete:"):
        st.session_state["assistant_messages"] = []
        st.rerun()
    examples_col.caption("Примеры: " + " · ".join(FULL_EXAMPLES))
    history = st.session_state.setdefault("assistant_messages", [])
    for message in history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    question = st.chat_input("Спросите о рассчитанных показателях")
    if question:
        with st.chat_message("user"):
            st.write(question)
        try:
            with st.spinner("Готовлю ответ..."):
                answer = service.ask(question, st.session_state["financial_context"], history[-6:])
        except (AIServiceError, ValueError) as error:
            st.error(str(error))
            return
        history.extend(({"role": "user", "content": question}, {"role": "assistant", "content": answer}))
        with st.chat_message("assistant"):
            st.write(answer)
