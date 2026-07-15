"""Pure, testable calculations for the trade acquiring prototype."""

from collections.abc import Iterable

from schemas.tariff import AcquiringCostBreakdown, AcquiringForecast, AcquiringInput, AcquiringTariffRule, TariffRecommendation, TerminalTurnoverCheck


def _validate_non_negative(**values: float | int) -> None:
    """Reject negative money amounts and terminal counts with a clear error."""
    for name, value in values.items():
        if value < 0:
            raise ValueError(f"{name} не может быть отрицательным.")


def get_applicable_rate(rules: Iterable[AcquiringTariffRule], acquiring_input: AcquiringInput) -> AcquiringTariffRule | None:
    """Return the rule matching product, tariff, industry, mode and card turnover."""
    _validate_non_negative(card_turnover=acquiring_input.card_turnover)
    matches = [rule for rule in rules if rule.product_type == acquiring_input.product_type and rule.tariff_name == acquiring_input.tariff_name and rule.industry_group == acquiring_input.industry_group and rule.settlement_mode == acquiring_input.settlement_mode and acquiring_input.card_turnover >= rule.turnover_min and (rule.turnover_max is None or acquiring_input.card_turnover < rule.turnover_max)]
    if len(matches) > 1:
        raise ValueError("Для выбранных параметров найдено несколько пересекающихся тарифных правил.")
    return matches[0] if matches else None


def calculate_card_commission(card_turnover: float, rate_percent: float | None) -> float:
    """Calculate card acquiring commission excluding VAT."""
    _validate_non_negative(card_turnover=card_turnover)
    if rate_percent is None:
        return 0.0
    _validate_non_negative(rate_percent=rate_percent)
    return card_turnover * rate_percent / 100


def calculate_vat(card_commission: float, vat_rate: float = 22.0) -> float:
    """Calculate VAT on card commission only, never on the additional fee."""
    _validate_non_negative(card_commission=card_commission, vat_rate=vat_rate)
    return card_commission * vat_rate / 100


def get_eligible_terminal_count(acquiring_input: AcquiringInput) -> int:
    """Count only terminal types covered by the minimum-turnover condition."""
    _validate_non_negative(pos_count=acquiring_input.pos_count, pin_pad_count=acquiring_input.pin_pad_count, cashbox_3in1_count=acquiring_input.cashbox_3in1_count, alfapos_count=acquiring_input.alfapos_count, ownpos_count=acquiring_input.ownpos_count, mpos_count=acquiring_input.mpos_count)
    return acquiring_input.pos_count + acquiring_input.pin_pad_count + acquiring_input.cashbox_3in1_count


def calculate_average_turnover_per_terminal(eligible_turnover: float, eligible_terminal_count: int) -> float | None:
    """Return average eligible turnover, avoiding division by zero."""
    _validate_non_negative(eligible_turnover=eligible_turnover, eligible_terminal_count=eligible_terminal_count)
    return eligible_turnover / eligible_terminal_count if eligible_terminal_count else None


def calculate_additional_fee(eligible_terminal_count: int, has_operations: bool, average_turnover_per_terminal: float | None, minimum_turnover_per_terminal: float, additional_fee_per_terminal: float) -> float:
    """Apply the non-VAT fee only for active eligible terminals below the threshold."""
    _validate_non_negative(eligible_terminal_count=eligible_terminal_count, minimum_turnover_per_terminal=minimum_turnover_per_terminal, additional_fee_per_terminal=additional_fee_per_terminal)
    if not has_operations or not eligible_terminal_count or average_turnover_per_terminal is None:
        return 0.0
    return additional_fee_per_terminal * eligible_terminal_count if average_turnover_per_terminal < minimum_turnover_per_terminal else 0.0


def calculate_effective_rate(total_known_cost: float, card_turnover: float) -> float | None:
    """Return known cost as a percentage of card turnover, or no value for zero turnover."""
    _validate_non_negative(total_known_cost=total_known_cost, card_turnover=card_turnover)
    return total_known_cost / card_turnover * 100 if card_turnover else None


def calculate_acquiring_costs(rules: Iterable[AcquiringTariffRule], acquiring_input: AcquiringInput) -> AcquiringCostBreakdown:
    """Calculate confirmed card-acquiring costs for the selected configuration."""
    _validate_non_negative(card_turnover=acquiring_input.card_turnover, sbp_turnover=acquiring_input.sbp_turnover)
    rule = get_applicable_rate(rules, acquiring_input)
    eligible_count = get_eligible_terminal_count(acquiring_input)
    eligible_turnover = acquiring_input.card_turnover + acquiring_input.sbp_turnover
    minimum = rule.min_turnover_per_terminal if rule else 600_000.0
    fee_per_terminal = rule.additional_fee if rule else 1_290.0
    vat_rate = rule.vat_rate if rule else 22.0
    average = calculate_average_turnover_per_terminal(eligible_turnover, eligible_count)
    additional_fee = calculate_additional_fee(eligible_count, acquiring_input.has_operations, average, minimum, fee_per_terminal)
    condition_met = None if not eligible_count or not acquiring_input.has_operations else bool(average is not None and average >= minimum)
    missing = max(0.0, minimum - average) if average is not None else 0.0
    terminal_check = TerminalTurnoverCheck(eligible_count, eligible_turnover, average, minimum, missing, condition_met, bool(additional_fee))
    rate = rule.rate_percent if rule else None
    card_commission = calculate_card_commission(acquiring_input.card_turnover, rate)
    vat_amount = calculate_vat(card_commission, vat_rate)
    total = card_commission + vat_amount + additional_fee
    return AcquiringCostBreakdown(rate, card_commission, vat_rate, vat_amount, card_commission + vat_amount, additional_fee, total, calculate_effective_rate(total, acquiring_input.card_turnover), acquiring_input.card_turnover - card_commission - vat_amount, terminal_check, rate is not None)


def build_tariff_recommendations(acquiring_input: AcquiringInput, costs: AcquiringCostBreakdown, alternative_rate: float | None = None) -> TariffRecommendation:
    """Build practical configuration advice without selecting or changing a tariff."""
    messages: list[str] = []
    check = costs.terminal_check
    if not costs.rate_available:
        messages.append("Уточните отраслевую ставку по MCC: подтверждённая ставка для выбранного способа зачисления отсутствует.")
    if check.additional_fee_applies:
        target = check.minimum_turnover_per_terminal * check.eligible_terminal_count
        messages.append(f"Основной источник дополнительных расходов — недостаточный средний оборот на терминал. Для выполнения условия нужен общий учитываемый оборот не менее {target:,.0f} ₽.".replace(",", " "))
        messages.append("Проверьте, можно ли увеличить оборот на терминал или сократить количество неиспользуемых терминалов.")
    if acquiring_input.settlement_mode == "realtime":
        messages.append("Проверьте необходимость режима реального времени: онлайн-зачисление может увеличивать ставку комиссии.")
        if alternative_rate is not None and costs.rate_percent is not None:
            difference = calculate_card_commission(acquiring_input.card_turnover, costs.rate_percent - alternative_rate)
            if difference > 0:
                messages.append(f"После обработки операций дешевле онлайн-зачисления примерно на {difference:,.0f} ₽ в месяц без НДС.".replace(",", " "))
    if acquiring_input.sbp_turnover:
        messages.append("Проверьте фактическую комиссию СБП: она не включена в известные расходы.")
    messages.append("Смена тарифа или условий обслуживания автоматически не выполняется.")
    return TariffRecommendation(messages)


def calculate_forecast_costs(rules: Iterable[AcquiringTariffRule], acquiring_input: AcquiringInput, forecast_card_turnover: float, forecast_sbp_turnover: float, current_total_known_cost: float, assumption: str | None = None) -> AcquiringForecast:
    """Calculate future costs from supplied forecasts without creating a second forecast model."""
    _validate_non_negative(forecast_card_turnover=forecast_card_turnover, forecast_sbp_turnover=forecast_sbp_turnover, current_total_known_cost=current_total_known_cost)
    forecast_input = AcquiringInput(**{**acquiring_input.__dict__, "card_turnover": forecast_card_turnover, "sbp_turnover": forecast_sbp_turnover})
    costs = calculate_acquiring_costs(rules, forecast_input)
    return AcquiringForecast(forecast_card_turnover, forecast_sbp_turnover, costs, costs.total_known_cost - current_total_known_cost, assumption)
