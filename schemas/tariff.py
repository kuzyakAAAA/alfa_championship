"""Tariff calculation schemas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TariffData:
    name: str
    monthly_fee: float
    transfer_limit: int
    transfer_commission: float
    acquiring_commission: float
    description: str


@dataclass(frozen=True)
class TariffCost:
    tariff_name: str
    monthly_fee: float
    transfer_cost: float
    acquiring_cost: float
    total: float


@dataclass(frozen=True)
class TariffRecommendation:
    current_tariff: str
    recommended_tariff: str
    current_cost: float
    recommended_cost: float
    savings: float
    reason: str
    warnings: list[str]
