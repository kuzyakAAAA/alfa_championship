"""Curated beginner courses from the official Alfa-Course platform."""

from dataclasses import dataclass
from html import escape

import streamlit as st


@dataclass(frozen=True)
class Course:
    title: str
    category: str
    details: str
    description: str
    url: str


COURSES = (
    Course(
        title="Просто о сложном: первые шаги в бизнесе",
        category="Первые шаги",
        details="22 урока · 4,5 часа · бесплатно",
        description=(
            "От бизнес-идеи и анализа рынка до команды, финансов, cash flow "
            "и юнит-экономики."
        ),
        url="https://kurs.alfabank.ru/courses/prosto-o-slozhnom/",
    ),
    Course(
        title="Регистрация бизнеса: самозанятость, ИП или ООО",
        category="Регистрация",
        details="4 урока · 50 минут",
        description=(
            "Поможет сравнить формы ведения бизнеса, выбрать подходящую и "
            "разобраться в регистрации."
        ),
        url="https://kurs.alfabank.ru/courses/registratsiya-biznesa/",
    ),
    Course(
        title="Как самозанятому стать ИП",
        category="Регистрация",
        details="6 уроков · 50 минут · бесплатно",
        description=(
            "Когда пора переходить на ИП, как зарегистрироваться, открыть счёт "
            "и продолжить развитие бизнеса."
        ),
        url="https://kurs.alfabank.ru/courses/kak-samozanyatomu-stat-ip/",
    ),
    Course(
        title="Азбука приёма платежей",
        category="Финансы",
        details="25 уроков · 4 часа · бесплатно",
        description=(
            "Торговый и интернет-эквайринг, онлайн-кассы, СБП, комиссии, "
            "подключение и решение частых проблем."
        ),
        url="https://kurs.alfabank.ru/courses/azbuka-priyoma-platezhej/",
    ),
    Course(
        title="Маркетплейсы: с чего начать и как преуспеть",
        category="Продажи",
        details="8 уроков · 2 часа · бесплатно",
        description=(
            "Выбор товара и стратегии, бизнес-модель, юнит-экономика, "
            "ценообразование и аналитика продаж."
        ),
        url="https://kurs.alfabank.ru/courses/marketpleysy-s-chego-nachat-kak-preuspet/",
    ),
    Course(
        title="Кейсы предпринимателей: как справиться с вызовами",
        category="Практика",
        details="5 уроков · 50 минут · бесплатно",
        description=(
            "Реальные задачи малого бизнеса: продажи, федеральное развитие, "
            "клиентская база и продвижение."
        ),
        url=(
            "https://kurs.alfabank.ru/courses/"
            "keysy-predprinimateley-kak-spravitsya-s-vyzovami-v-biznese/"
        ),
    ),
)

CATALOG_URL = "https://kurs.alfabank.ru/courses/"


def render_page() -> None:
    """Render a filterable grid whose cards open official course pages."""

    _render_styles()
    st.markdown(
        '<div class="ab-page-meta">Официальная платформа Альфа-Курс</div>',
        unsafe_allow_html=True,
    )
    st.title("Курсы для начинающих предпринимателей")
    st.write(
        "Практические материалы для тех, кто запускает бизнес или делает "
        "первые шаги в управлении им."
    )

    categories = ["Все", *dict.fromkeys(course.category for course in COURSES)]
    selected = st.selectbox("Направление", categories)
    visible = [
        course for course in COURSES if selected == "Все" or course.category == selected
    ]
    for offset in range(0, len(visible), 3):
        columns = st.columns(3)
        for column, course in zip(columns, visible[offset : offset + 3], strict=False):
            column.markdown(course_card_html(course), unsafe_allow_html=True)

    st.caption(
        "При выборе курса откроется официальный сайт Альфа-Курс в новой вкладке. "
        "Условия доступа и стоимость проверяйте на странице курса."
    )
    st.link_button(
        "Посмотреть все курсы Альфа-Банка",
        CATALOG_URL,
        icon=":material/open_in_new:",
    )


def course_card_html(course: Course) -> str:
    """Build one safe, fully clickable external course card."""

    title = escape(course.title)
    return f"""
        <a class="ab-course-card" href="{escape(course.url, quote=True)}"
           target="_blank" rel="noopener noreferrer" aria-label="Открыть курс {title}">
            <span class="ab-course-card__category">{escape(course.category)}</span>
            <span class="ab-course-card__title">{title}</span>
            <span class="ab-course-card__details">{escape(course.details)}</span>
            <span class="ab-course-card__description">{escape(course.description)}</span>
            <span class="ab-course-card__action">Открыть курс ↗</span>
        </a>
    """


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .ab-course-card {
            display: flex;
            min-height: 285px;
            height: calc(100% - 1rem);
            flex-direction: column;
            gap: 0.8rem;
            margin: 0.45rem 0 1rem;
            padding: 1.35rem;
            color: #111111 !important;
            text-decoration: none !important;
            background: #FFFFFF;
            border: 1px solid #E8E8E8;
            border-top: 4px solid #EF3124;
            border-radius: 8px;
            transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
        }
        .ab-course-card:hover {
            transform: translateY(-3px);
            border-color: #D8D8D8;
            box-shadow: 0 12px 28px rgba(17, 17, 17, 0.10);
        }
        .ab-course-card:focus-visible {
            outline: 3px solid rgba(239, 49, 36, 0.35);
            outline-offset: 3px;
        }
        .ab-course-card__category {
            align-self: flex-start;
            padding: 0.3rem 0.55rem;
            color: #D91F14;
            background: #FFF1F0;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 750;
            text-transform: uppercase;
        }
        .ab-course-card__title {
            font-size: 1.15rem;
            font-weight: 760;
            line-height: 1.25;
        }
        .ab-course-card__details {
            color: #555555;
            font-size: 0.8rem;
            font-weight: 650;
        }
        .ab-course-card__description {
            color: #6B6B6B;
            font-size: 0.88rem;
            line-height: 1.5;
        }
        .ab-course-card__action {
            margin-top: auto;
            color: #EF3124;
            font-size: 0.86rem;
            font-weight: 750;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
