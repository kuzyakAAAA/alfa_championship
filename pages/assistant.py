"""Financial assistant chat page."""

import pandas as pd
import streamlit as st

from config import LLM_API_KEY
from services.ai_service import answer_question, prepare_ai_context
from services.analytics_service import calculate_metrics
from services.anomaly_service import detect_anomalies


EXAMPLES = [
    "Какая у меня прибыль?",
    "Что происходит с расходами?",
    "Какие финансовые риски обнаружены?",
]


def render_page(frame: pd.DataFrame) -> None:
    """Render a session-based context-bound chat."""

    st.title("ИИ-помощник")
    if not LLM_API_KEY:
        st.info("API-ключ не задан: помощник работает в безопасном mock-режиме.")
    st.caption("Примеры: " + " · ".join(EXAMPLES))
    history = st.session_state.setdefault("chat_history", [])
    for message in history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    question = st.chat_input("Спросите о рассчитанных показателях")
    if question:
        context = prepare_ai_context(calculate_metrics(frame), detect_anomalies(frame))
        answer = answer_question(question, context, LLM_API_KEY)
        history.extend(({"role": "user", "content": question}, {"role": "assistant", "content": answer}))
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.write(answer)
