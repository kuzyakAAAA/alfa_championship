"""Trade acquiring calculator page."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from repositories.tariff_repository import load_tariff_rules
from schemas.tariff import AcquiringInput
from services.analytics_service import calculate_revenue
from services.forecast_service import build_revenue_forecast
from services.tariff_service import build_tariff_recommendations, calculate_acquiring_costs, calculate_forecast_costs, get_applicable_rate
from utils.formatting import format_percent, format_rubles
from utils.style import ALFA_RED, frame_period, render_page_heading, style_plotly_figure


INDUSTRIES = {
    "Обычный бизнес": ("general", "Не задано"),
    "ЖКХ": ("housing_utilities", "4900, 4814"),
    "Образование и часть медицинских услуг": ("education_medical", "8211, 8220, 8011"),
    "Туризм и продажа автомобилей": ("tourism_auto", "4722, 7011, 5511"),
    "Быстрое питание": ("fast_food", "5814"),
    "Дополнительное образование и отдельные медицинские услуги": ("extra_education_medical", "8299, 8099"),
    "Стоматология, такси, аптеки, АЗС и недвижимость": ("special_services", "8021, 4121, 5912, 5541, 6513"),
    "Супермаркеты и кейтеринг": ("supermarkets_catering", "5411, 5811"),
    "Рестораны и кафе": ("restaurants_cafes", "5812, 5813"),
}
MODES = {"После обработки операций": "standard", "В режиме реального времени": "realtime"}


def _forecast_turnover(frame: pd.DataFrame, card_turnover: float, sbp_turnover: float) -> tuple[float, float, str] | None:
    """Use the existing revenue forecast and explicitly retain the current channel split."""
    result = build_revenue_forecast(frame, periods=1)
    if not result.sufficient_history or not result.scenarios or not result.scenarios[1].points:
        return None
    total_forecast = result.scenarios[1].points[0].value
    current_total = card_turnover + sbp_turnover
    if not current_total:
        return None
    card_share = card_turnover / current_total
    return total_forecast * card_share, total_forecast * (1 - card_share), "Прогноз выручки не разделяет карты и СБП; использована текущая доля каждого канала."


def _render_terminal_check(costs: object, has_operations: bool) -> None:
    """Render the terminal condition outcome from the calculated breakdown."""
    check = costs.terminal_check  # type: ignore[attr-defined]
    st.subheader("Проверка минимального оборота")
    if not check.eligible_terminal_count:
        st.info("В расчёте нет POS-терминалов, PIN PAD или касс 3в1, поэтому проверка минимального оборота не применяется.")
        return
    if not has_operations:
        st.info("В текущем месяце операции отсутствовали. Дополнительная комиссия за недостаточный оборот в демонстрационном расчёте не начисляется.")
        return
    columns = st.columns(4)
    columns[0].metric("Учитываемый оборот", format_rubles(check.eligible_turnover))
    columns[1].metric("Учитываемые терминалы", str(check.eligible_terminal_count))
    columns[2].metric("Средний оборот", format_rubles(check.average_turnover_per_terminal))
    columns[3].metric("Требование", format_rubles(check.minimum_turnover_per_terminal))
    if check.condition_met:
        st.success(f"Средний оборот на один учитываемый терминал составляет {format_rubles(check.average_turnover_per_terminal)}. Требование {format_rubles(check.minimum_turnover_per_terminal)} выполнено.")
    else:
        fee = "" if not check.additional_fee_applies else f" Возможна дополнительная комиссия {format_rubles(costs.additional_fee)}."  # type: ignore[attr-defined]
        st.warning(f"Средний оборот на один терминал составляет {format_rubles(check.average_turnover_per_terminal)} — на {format_rubles(check.missing_turnover)} ниже минимального значения.{fee}")


def render_page(frame: pd.DataFrame, tariff_frame: pd.DataFrame | None = None) -> None:
    """Render the acquiring cost calculator; ``tariff_frame`` remains a compatible argument."""
    del tariff_frame
    rules = load_tariff_rules()
    render_page_heading("Тарифы", len(frame), frame_period(frame))
    st.write("Раздел рассчитывает ориентировочную стоимость торгового эквайринга по выбранным параметрам. Расчёт не является индивидуальным предложением банка.")
    st.info("В прототипе используются условия из открытых тарифных документов Альфа-Банка. Итоговые условия конкретного клиента могут зависеть от договора, даты подключения, MCC-кода, способа расчётов и индивидуальных условий.")
    st.caption("Расчётная модель подготовлена по открытым тарифным документам с редакцией от 01.06.2026.")

    st.subheader("Параметры бизнеса")
    product_col, tariff_col = st.columns(2)
    product_col.selectbox("Вид продукта", ["Торговый эквайринг"], disabled=True)
    product_col.caption("Интернет-эквайринг будет добавлен позже.")
    tariff_col.selectbox("Тариф", ["Продвинутый"], disabled=True)
    industry_label = st.selectbox("Отрасль или MCC-группа", list(INDUSTRIES))
    industry_group, mcc_codes = INDUSTRIES[industry_label]
    st.caption(f"MCC-коды группы: {mcc_codes}")
    mode_label = st.selectbox("Способ зачисления", list(MODES))
    st.caption("Онлайн-зачисление может увеличивать ставку комиссии. Для отдельных видов деятельности оно может быть недоступно.")
    settlement_mode = MODES[mode_label]
    provisional = AcquiringInput("trade", "Продвинутый", industry_group, settlement_mode, 0, 0)
    selected_rule = get_applicable_rate(rules, provisional)
    if selected_rule is not None and selected_rule.rate_percent is None:
        st.warning("Для выбранной отрасли в прототипе отсутствует подтверждённая ставка онлайн-зачисления.")

    default_turnover = max(0.0, float(calculate_revenue(frame)))
    turnover_col, sbp_col, operations_col = st.columns(3)
    card_turnover = float(turnover_col.number_input("Оборот по картам, ₽", min_value=0.0, value=default_turnover, step=10_000.0))
    turnover_col.caption("Значение взято из доходных операций как демонстрационный ориентир.")
    sbp_turnover = float(sbp_col.number_input("Оборот через СБП и Pay-сервисы, ₽", min_value=0.0, value=0.0, step=10_000.0))
    sbp_col.caption("СБП учитывается в обороте терминалов, но НДС на него не начисляется.")
    has_operations = operations_col.toggle("Были операции в текущем месяце", value=bool((frame["operation_type"] == "income").any()))

    st.markdown("#### Терминалы")
    terminal_columns = st.columns(3)
    pos_count = int(terminal_columns[0].number_input("POS-терминалы", min_value=0, value=1, step=1))
    pin_pad_count = int(terminal_columns[1].number_input("PIN PAD", min_value=0, value=0, step=1))
    cashbox_count = int(terminal_columns[2].number_input("Кассы 3в1", min_value=0, value=0, step=1))
    terminal_columns = st.columns(3)
    alfapos_count = int(terminal_columns[0].number_input("AlfaPOS", min_value=0, value=0, step=1))
    ownpos_count = int(terminal_columns[1].number_input("OWNPOS", min_value=0, value=0, step=1))
    mpos_count = int(terminal_columns[2].number_input("MPOS", min_value=0, value=0, step=1))
    acquiring_input = AcquiringInput("trade", "Продвинутый", industry_group, settlement_mode, card_turnover, sbp_turnover, pos_count, pin_pad_count, cashbox_count, alfapos_count, ownpos_count, mpos_count, has_operations)
    costs = calculate_acquiring_costs(rules, acquiring_input)
    if not costs.terminal_check.eligible_terminal_count:
        st.warning("Выбрано ноль учитываемых терминалов: проверка оборота на терминал не выполняется.")

    st.subheader("Расчёт текущего месяца")
    metrics = st.columns(4)
    metrics[0].metric("Тарифная ставка", format_percent(costs.rate_percent) if costs.rate_available else "нет данных")
    metrics[1].metric("Карточная комиссия без НДС", format_rubles(costs.card_commission))
    metrics[2].metric("НДС", format_rubles(costs.vat_amount))
    metrics[3].metric("Дополнительная комиссия", format_rubles(costs.additional_fee))
    metrics = st.columns(3)
    metrics[0].metric("Известные расходы за месяц", format_rubles(costs.total_known_cost))
    metrics[1].metric("Эффективная ставка", format_percent(costs.effective_rate) if costs.effective_rate is not None else "-")
    metrics[2].metric("К зачислению по карточным операциям", format_rubles(costs.net_card_settlement))
    if not costs.rate_available:
        st.error("Карточная комиссия не включена в итоговую стоимость: для выбранного сочетания отрасли и способа зачисления нет подтверждённой ставки.")
    if sbp_turnover:
        st.caption("Комиссия СБП не включена в итоговую стоимость, так как её размер зависит от вида деятельности и условий договора.")

    st.subheader("Структура расходов")
    table = pd.DataFrame([
        {"Компонент": "Карточная комиссия", "Сумма": format_rubles(costs.card_commission), "Пояснение": "Оборот × тарифная ставка"},
        {"Компонент": "НДС", "Сумма": format_rubles(costs.vat_amount), "Пояснение": "22% от карточной комиссии"},
        {"Компонент": "Дополнительная комиссия", "Сумма": format_rubles(costs.additional_fee), "Пояснение": "За недостаточный средний оборот"},
        {"Компонент": "Итого известных расходов", "Сумма": format_rubles(costs.total_known_cost), "Пояснение": "Без неподтверждённой комиссии СБП"},
    ])
    st.dataframe(table, width="stretch", hide_index=True)
    chart_values = [("Карточная комиссия", costs.card_commission), ("НДС", costs.vat_amount), ("Дополнительная комиссия", costs.additional_fee)]
    chart_values = [(name, value) for name, value in chart_values if value]
    if chart_values:
        figure = go.Figure(go.Bar(x=[name for name, _ in chart_values], y=[value for _, value in chart_values], marker_color=ALFA_RED))
        figure.update_layout(title="Структура известных расходов", showlegend=False)
        st.plotly_chart(style_plotly_figure(figure), width="stretch")

    _render_terminal_check(costs, has_operations)
    st.subheader("Прогноз следующего месяца")
    forecast_values = _forecast_turnover(frame, card_turnover, sbp_turnover)
    if forecast_values is None:
        st.info("Недостаточно данных для прогноза расходов на эквайринг.")
    else:
        forecast_card, forecast_sbp, assumption = forecast_values
        forecast = calculate_forecast_costs(rules, acquiring_input, forecast_card, forecast_sbp, costs.total_known_cost, assumption)
        st.caption(assumption)
        prediction = st.columns(4)
        prediction[0].metric("Прогноз карточной комиссии", format_rubles(forecast.costs.card_commission))
        prediction[1].metric("Прогноз НДС", format_rubles(forecast.costs.vat_amount))
        prediction[2].metric("Прогноз известных расходов", format_rubles(forecast.costs.total_known_cost), format_rubles(forecast.cost_difference))
        average = forecast.costs.terminal_check.average_turnover_per_terminal
        prediction[3].metric("Прогноз оборота на терминал", format_rubles(average) if average is not None else "-")
        if forecast.costs.terminal_check.additional_fee_applies:
            st.warning("В прогнозе возможна дополнительная комиссия за недостаточный оборот на терминал.")

    alternative = AcquiringInput("trade", "Продвинутый", industry_group, "standard", card_turnover, sbp_turnover)
    alternative_rule = get_applicable_rate(rules, alternative)
    recommendation = build_tariff_recommendations(acquiring_input, costs, alternative_rule.rate_percent if alternative_rule else None)
    st.subheader("Рекомендации")
    for message in recommendation.messages:
        st.write("• " + message)
    st.subheader("Пояснение методики расчёта")
    st.caption("Карточная комиссия = оборот по картам × ставка. НДС = 22% от карточной комиссии. Дополнительная комиссия не облагается НДС и применяется только к POS, PIN PAD и кассам 3в1 при недостаточном обороте и наличии операций.")
    st.session_state["tariff_recommendation"] = {"product_type": "Торговый эквайринг", "tariff_name": "Продвинутый", "rate_percent": costs.rate_percent, "card_commission": costs.card_commission, "vat_amount": costs.vat_amount, "additional_fee": costs.additional_fee, "total_known_cost": costs.total_known_cost, "effective_rate": costs.effective_rate, "turnover_condition_met": costs.terminal_check.condition_met, "automatic_change": False}
