"""Tests for confirmed trade acquiring calculations."""

import pytest

from repositories.tariff_repository import load_tariff_rules
from schemas.tariff import AcquiringInput
from services.tariff_service import calculate_acquiring_costs, calculate_card_commission, calculate_effective_rate, calculate_forecast_costs, calculate_vat, get_applicable_rate


@pytest.fixture
def rules():
    return load_tariff_rules()


def input_data(**changes):
    values = dict(product_type="trade", tariff_name="Продвинутый", industry_group="general", settlement_mode="standard", card_turnover=900_000, sbp_turnover=100_000, pos_count=2, has_operations=True)
    values.update(changes)
    return AcquiringInput(**values)


def test_general_rate_below_two_million(rules) -> None:
    assert get_applicable_rate(rules, input_data()).rate_percent == 1.99


def test_general_rate_from_two_million(rules) -> None:
    assert get_applicable_rate(rules, input_data(card_turnover=2_000_000)).rate_percent == 2.30


def test_realtime_and_industry_rates(rules) -> None:
    assert get_applicable_rate(rules, input_data(settlement_mode="realtime")).rate_percent == 2.19
    assert get_applicable_rate(rules, input_data(industry_group="housing_utilities")).rate_percent == 0.95


def test_control_scenario(rules) -> None:
    costs = calculate_acquiring_costs(rules, input_data())
    assert costs.card_commission == pytest.approx(17_910)
    assert costs.vat_amount == pytest.approx(3_940.2)
    assert costs.additional_fee == pytest.approx(2_580)
    assert costs.total_known_cost == pytest.approx(24_430.2)
    assert costs.effective_rate == pytest.approx(2.714466, rel=1e-4)
    assert costs.terminal_check.average_turnover_per_terminal == pytest.approx(500_000)


def test_vat_and_effective_rate_helpers() -> None:
    assert calculate_card_commission(100_000, 1.99) == pytest.approx(1_990)
    assert calculate_vat(1_990) == pytest.approx(437.8)
    assert calculate_effective_rate(2_427.8, 100_000) == pytest.approx(2.4278)
    assert calculate_effective_rate(1, 0) is None


def test_no_additional_fee_without_operations_or_eligible_terminal(rules) -> None:
    assert calculate_acquiring_costs(rules, input_data(has_operations=False)).additional_fee == 0
    assert calculate_acquiring_costs(rules, input_data(pos_count=0, alfapos_count=3)).additional_fee == 0


@pytest.mark.parametrize("field", ["alfapos_count", "ownpos_count", "mpos_count"])
def test_non_eligible_terminal_types_do_not_increase_fee(rules, field: str) -> None:
    costs = calculate_acquiring_costs(rules, input_data(card_turnover=400_000, sbp_turnover=0, pos_count=1, **{field: 5}))
    assert costs.additional_fee == 1_290


def test_unknown_rate_is_not_invented(rules) -> None:
    costs = calculate_acquiring_costs(rules, input_data(industry_group="restaurants_cafes", settlement_mode="realtime"))
    assert not costs.rate_available
    assert costs.rate_percent is None
    assert costs.card_commission == 0


def test_negative_values_raise_error(rules) -> None:
    with pytest.raises(ValueError, match="card_turnover"):
        calculate_acquiring_costs(rules, input_data(card_turnover=-1))
    with pytest.raises(ValueError, match="pos_count"):
        calculate_acquiring_costs(rules, input_data(pos_count=-1))


def test_forecast_uses_supplied_values(rules) -> None:
    current = calculate_acquiring_costs(rules, input_data())
    forecast = calculate_forecast_costs(rules, input_data(), 1_200_000, 0, current.total_known_cost)
    assert forecast.card_turnover == 1_200_000
    assert forecast.costs.card_commission == pytest.approx(23_880)
