"""Streamlit entry point for Alfa Business AI."""

import pandas as pd
import streamlit as st

from config import APP_NAME, DATA_DIR
from pages import analytics, assistant, dashboard, forecast, tariffs
from services.transaction_service import clean_transactions
from utils.file_loader import load_csv_file
from utils.style import apply_global_styles


st.set_page_config(page_title=APP_NAME, page_icon=":material/monitoring:", layout="wide")
apply_global_styles()


@st.cache_data
def load_demo_data() -> pd.DataFrame:
    """Load and normalize bundled fictional transactions."""

    return clean_transactions(load_csv_file(DATA_DIR / "demo_transactions.csv"))


@st.cache_data
def load_tariffs() -> pd.DataFrame:
    """Load bundled demonstration tariffs."""

    return pd.read_csv(DATA_DIR / "tariffs.csv")


def main() -> None:
    """Compose navigation, data source controls and the selected page."""

    st.sidebar.markdown(
        """
        <div class="ab-brand">
            <div class="ab-brand__mark">A</div>
            <div class="ab-brand__name">Альфа Бизнес AI<span>Финансовая аналитика</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="ab-sidebar-label">Разделы</div>', unsafe_allow_html=True)
    page = st.sidebar.radio(
        "Навигация",
        ["Главная", "Аналитика", "Прогноз", "Тарифы", "ИИ-помощник"],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.markdown('<div class="ab-sidebar-label">Источник данных</div>', unsafe_allow_html=True)
    demo_mode = st.sidebar.toggle("Демонстрационный режим", value=True)
    uploaded = None
    if not demo_mode:
        uploaded = st.sidebar.file_uploader("Операции CSV", type=["csv"])
    try:
        if demo_mode or uploaded is None:
            frame = load_demo_data()
            st.sidebar.caption("Используются вымышленные демонстрационные данные.")
        else:
            frame = clean_transactions(load_csv_file(uploaded))
            st.sidebar.success(f"Загружено операций: {len(frame)}")
    except (ValueError, OSError, pd.errors.ParserError) as error:
        st.error(f"Не удалось обработать файл: {error}")
        st.stop()
    renderers = {
        "Главная": lambda: dashboard.render_page(frame),
        "Аналитика": lambda: analytics.render_page(frame),
        "Прогноз": lambda: forecast.render_page(frame),
        "Тарифы": lambda: tariffs.render_page(frame, load_tariffs()),
        "ИИ-помощник": lambda: assistant.render_page(frame, load_tariffs()),
    }
    renderers[page]()


if __name__ == "__main__":
    main()
