"""Shared visual theme for the Streamlit interface."""

from html import escape

import plotly.graph_objects as go
import pandas as pd
import streamlit as st


ALFA_RED = "#EF3124"
ALFA_RED_DARK = "#D91F14"
INK = "#111111"
MUTED = "#6B6B6B"
GRID = "#E9E9E9"
SURFACE = "#FFFFFF"


def apply_global_styles() -> None:
    """Apply the red, white and black application theme."""

    st.markdown(
        """
        <style>
        :root {
            --alfa-red: #EF3124;
            --alfa-red-dark: #D91F14;
            --alfa-ink: #111111;
            --alfa-muted: #6B6B6B;
            --alfa-line: #E8E8E8;
            --alfa-soft: #F5F5F5;
            --alfa-white: #FFFFFF;
        }

        html, body {
            font-family: Inter, Arial, Helvetica, sans-serif;
            letter-spacing: 0;
        }

        .stApp {
            background: var(--alfa-white);
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.96);
            border-bottom: 1px solid var(--alfa-line);
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        [data-testid="stSidebar"] {
            background: var(--alfa-white);
            border-right: 1px solid var(--alfa-line);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.2rem;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding-left: 0.65rem;
            padding-right: 0.65rem;
        }

        .ab-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            min-height: 3.25rem;
            padding: 0 0.65rem 1rem;
            border-bottom: 1px solid var(--alfa-line);
            margin-bottom: 1rem;
        }

        .ab-brand__mark {
            display: grid;
            place-items: center;
            width: 2.25rem;
            height: 2.25rem;
            flex: 0 0 2.25rem;
            background: var(--alfa-red);
            color: var(--alfa-white);
            border-radius: 6px;
            font-size: 1.2rem;
            font-weight: 800;
        }

        .ab-brand__name {
            color: var(--alfa-ink);
            font-size: 1rem;
            font-weight: 750;
            line-height: 1.1;
        }

        .ab-brand__name span {
            display: block;
            margin-top: 0.25rem;
            color: var(--alfa-muted);
            font-size: 0.7rem;
            font-weight: 500;
        }

        .ab-sidebar-label {
            padding: 0.2rem 0.65rem 0.4rem;
            color: #898989;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        [data-testid="stSidebar"] [role="radiogroup"] {
            gap: 0.3rem;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            min-height: 2.65rem;
            padding: 0.65rem 0.75rem;
            border-radius: 7px;
            transition: background-color 120ms ease, color 120ms ease;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
            display: none;
        }

        [data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"] > div:first-child {
            display: none !important;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: #F4F4F4;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: var(--alfa-red);
            color: var(--alfa-white);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
            color: var(--alfa-white);
            font-weight: 700;
        }

        [data-testid="stSidebar"] [role="radiogroup"] [data-testid="stMarkdownContainer"] p {
            font-size: 0.9rem;
            overflow-wrap: anywhere;
        }

        [data-testid="stSidebar"] [data-testid="stFileUploader"] {
            border: 1px solid var(--alfa-line);
            border-radius: 7px;
            padding: 0.2rem;
        }

        [data-testid="stSidebar"] hr {
            border-color: var(--alfa-line);
            margin: 1rem 0;
        }

        .block-container {
            max-width: 1440px;
            padding-top: 4.2rem !important;
            padding-bottom: 3rem;
            padding-left: clamp(1.1rem, 3vw, 3.5rem);
            padding-right: clamp(1.1rem, 3vw, 3.5rem);
        }

        .ab-page-meta {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin-bottom: 0.25rem;
            color: var(--alfa-muted);
            font-size: 0.78rem;
            font-weight: 600;
        }

        .ab-page-meta::before {
            content: "";
            width: 1.5rem;
            height: 3px;
            background: var(--alfa-red);
        }

        h1 {
            margin: 0 0 1.4rem !important;
            color: var(--alfa-ink) !important;
            font-size: clamp(2rem, 3vw, 2.8rem) !important;
            font-weight: 760 !important;
            line-height: 1.08 !important;
            letter-spacing: 0 !important;
        }

        h2, h3 {
            color: var(--alfa-ink) !important;
            font-weight: 720 !important;
            letter-spacing: 0 !important;
        }

        h2 { font-size: 1.35rem !important; }
        h3 { font-size: 1.05rem !important; }

        [data-testid="stMetric"] {
            min-height: 8.2rem;
            padding: 1.15rem 1.2rem;
            background: var(--alfa-white);
            border: 1px solid var(--alfa-line);
            border-top: 3px solid var(--alfa-red);
            border-radius: 7px;
        }

        [data-testid="stMetricLabel"] p {
            color: var(--alfa-muted);
            font-size: 0.78rem;
            font-weight: 650;
        }

        [data-testid="stMetricValue"] {
            color: var(--alfa-ink);
            font-size: clamp(1.45rem, 2vw, 2rem);
            font-weight: 760;
            overflow-wrap: anywhere;
        }

        [data-testid="stMetricDelta"] {
            font-size: 0.75rem;
            font-weight: 650;
        }

        [data-testid="stPlotlyChart"] {
            overflow: hidden;
            border: 1px solid var(--alfa-line);
            border-radius: 7px;
        }

        [data-testid="stDataFrame"] {
            overflow: hidden;
            border: 1px solid var(--alfa-line);
            border-radius: 7px;
        }

        [data-testid="stDataFrame"] [role="columnheader"],
        [data-testid="stDataFrame"] [role="gridcell"] {
            white-space: normal;
            overflow-wrap: anywhere;
        }

        .stButton > button, [data-testid="stFileUploader"] button {
            min-height: 2.5rem;
            background: var(--alfa-red);
            color: var(--alfa-white);
            border: 1px solid var(--alfa-red);
            border-radius: 7px;
            font-weight: 700;
        }

        .stButton > button:hover, [data-testid="stFileUploader"] button:hover {
            background: var(--alfa-red-dark);
            color: var(--alfa-white);
            border-color: var(--alfa-red-dark);
        }

        [data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stChatInput"] textarea {
            border-color: #D7D7D7 !important;
            border-radius: 7px !important;
            box-shadow: none !important;
        }

        [data-baseweb="select"] > div:focus-within,
        [data-testid="stDateInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stChatInput"] textarea:focus {
            border-color: var(--alfa-red) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 7px;
            border-left-width: 4px;
        }

        [data-testid="stAlert"] p {
            color: inherit;
        }

        [data-testid="stChatMessage"] {
            border: 1px solid var(--alfa-line);
            border-radius: 7px;
            background: var(--alfa-white);
        }

        [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"] {
            background: var(--alfa-red);
        }

        [data-testid="stToggle"] input:checked + div {
            background: var(--alfa-red) !important;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-top: 3.8rem !important;
            }

            [data-testid="stMetric"] {
                min-height: 7.4rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_heading(title: str, frame_rows: int, period: str) -> None:
    """Render a compact data context line and page title."""

    st.markdown(
        f'<div class="ab-page-meta">{escape(period)} · {frame_rows} операций</div>',
        unsafe_allow_html=True,
    )
    st.title(title)


def frame_period(frame: pd.DataFrame) -> str:
    """Return the visible date range of a transaction frame."""

    if frame.empty:
        return "Нет данных"
    dates = pd.to_datetime(frame["date"])
    return f"{dates.min():%d.%m.%Y} — {dates.max():%d.%m.%Y}"


def style_plotly_figure(figure: go.Figure) -> go.Figure:
    """Apply the shared chart typography, spacing and grid treatment."""

    figure.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font={"family": "Inter, Arial, sans-serif", "color": INK, "size": 12},
        margin={"l": 34, "r": 24, "t": 38, "b": 68},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "title": None,
        },
        hoverlabel={"bgcolor": INK, "font_color": SURFACE, "bordercolor": INK},
        separators=", ",
    )
    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=GRID,
        tickfont={"color": MUTED},
        tickangle=-30,
        automargin=True,
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        tickfont={"color": MUTED},
        tickformat=",d",
        automargin=True,
    )
    return figure
