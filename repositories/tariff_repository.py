"""Validated CSV access for acquiring tariff rules."""

from pathlib import Path

import pandas as pd

from config import DATA_DIR
from schemas.tariff import AcquiringInput, AcquiringTariffRule
from services.tariff_service import get_applicable_rate


REQUIRED_COLUMNS = {"product_type", "tariff_name", "industry_group", "mcc_codes", "turnover_min", "turnover_max", "settlement_mode", "rate_percent", "vat_rate", "additional_fee", "min_turnover_per_terminal", "effective_from", "source_note"}


def load_tariff_rules(csv_path: str | Path | None = None) -> list[AcquiringTariffRule]:
    """Load, validate and convert bundled tariff rules from UTF-8 CSV."""
    frame = pd.read_csv(csv_path or DATA_DIR / "tariffs.csv", keep_default_na=False)
    if frame.empty:
        raise ValueError("Файл тарифных правил пуст.")
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError("В тарифном CSV отсутствуют колонки: " + ", ".join(sorted(missing)))
    rules: list[AcquiringTariffRule] = []
    for row in frame.to_dict(orient="records"):
        try:
            maximum = float(row["turnover_max"]) if str(row["turnover_max"]).strip() else None
            rate = float(row["rate_percent"]) if str(row["rate_percent"]).strip() else None
            rule = AcquiringTariffRule(str(row["product_type"]), str(row["tariff_name"]), str(row["industry_group"]), str(row["mcc_codes"]), float(row["turnover_min"]), maximum, str(row["settlement_mode"]), rate, float(row["vat_rate"]), float(row["additional_fee"]), float(row["min_turnover_per_terminal"]), str(row["effective_from"]), str(row["source_note"]))
        except (TypeError, ValueError) as error:
            raise ValueError("В тарифном CSV указано некорректное число.") from error
        if rule.turnover_min < 0 or (rule.turnover_max is not None and rule.turnover_max <= rule.turnover_min):
            raise ValueError("В тарифном CSV указан некорректный диапазон оборота.")
        rules.append(rule)
    _validate_no_overlaps(rules)
    return rules


def _validate_no_overlaps(rules: list[AcquiringTariffRule]) -> None:
    """Fail early when ranges within a tariff dimension overlap."""
    for rule in rules:
        for other in rules:
            if rule is other or (rule.product_type, rule.tariff_name, rule.industry_group, rule.settlement_mode) != (other.product_type, other.tariff_name, other.industry_group, other.settlement_mode):
                continue
            rule_max = float("inf") if rule.turnover_max is None else rule.turnover_max
            other_max = float("inf") if other.turnover_max is None else other.turnover_max
            if rule.turnover_min < other_max and other.turnover_min < rule_max:
                raise ValueError("В тарифном CSV пересекаются диапазоны оборота.")


def get_rules_by_product(rules: list[AcquiringTariffRule], product_type: str) -> list[AcquiringTariffRule]:
    """Return rules for a product type."""
    return [rule for rule in rules if rule.product_type == product_type]


def get_rules_by_tariff(rules: list[AcquiringTariffRule], tariff_name: str) -> list[AcquiringTariffRule]:
    """Return rules for a tariff name."""
    return [rule for rule in rules if rule.tariff_name == tariff_name]


def get_rules_by_industry(rules: list[AcquiringTariffRule], industry_group: str) -> list[AcquiringTariffRule]:
    """Return rules for an industry group."""
    return [rule for rule in rules if rule.industry_group == industry_group]


def get_rule_for_input(rules: list[AcquiringTariffRule], acquiring_input: AcquiringInput) -> AcquiringTariffRule | None:
    """Find a matching rule for the given turnover and settlement mode."""
    return get_applicable_rate(rules, acquiring_input)


def has_applicable_rule(rules: list[AcquiringTariffRule], acquiring_input: AcquiringInput) -> bool:
    """Return whether a confirmed rate is available for the selected inputs."""
    rule = get_rule_for_input(rules, acquiring_input)
    return bool(rule and rule.rate_percent is not None)
