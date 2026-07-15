"""Typed structures for the acquiring cost calculator."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AcquiringTariffRule:
    """One confirmed acquiring condition loaded from the tariff data file."""
    product_type: str
    tariff_name: str
    industry_group: str
    mcc_codes: str
    turnover_min: float
    turnover_max: float | None
    settlement_mode: str
    rate_percent: float | None
    vat_rate: float
    additional_fee: float
    min_turnover_per_terminal: float
    effective_from: str
    source_note: str


@dataclass(frozen=True)
class AcquiringInput:
    """User-selected parameters for a monthly acquiring calculation."""
    product_type: str
    tariff_name: str
    industry_group: str
    settlement_mode: str
    card_turnover: float
    sbp_turnover: float
    pos_count: int = 0
    pin_pad_count: int = 0
    cashbox_3in1_count: int = 0
    alfapos_count: int = 0
    ownpos_count: int = 0
    mpos_count: int = 0
    has_operations: bool = True


@dataclass(frozen=True)
class TerminalTurnoverCheck:
    """Result of the minimum turnover check for eligible terminals."""
    eligible_terminal_count: int
    eligible_turnover: float
    average_turnover_per_terminal: float | None
    minimum_turnover_per_terminal: float
    missing_turnover: float
    condition_met: bool | None
    additional_fee_applies: bool


@dataclass(frozen=True)
class AcquiringCostBreakdown:
    """Known monthly acquiring costs; SBP pricing is intentionally excluded."""
    rate_percent: float | None
    card_commission: float
    vat_rate: float
    vat_amount: float
    card_commission_with_vat: float
    additional_fee: float
    total_known_cost: float
    effective_rate: float | None
    net_card_settlement: float
    terminal_check: TerminalTurnoverCheck
    rate_available: bool


@dataclass(frozen=True)
class AcquiringForecast:
    """Projection of the same calculation for a future month."""
    card_turnover: float
    sbp_turnover: float
    costs: AcquiringCostBreakdown
    cost_difference: float
    assumption: str | None = None


@dataclass(frozen=True)
class TariffRecommendation:
    """Non-binding configuration advice without an automatic tariff change."""
    messages: list[str]
    automatic_change: bool = False
