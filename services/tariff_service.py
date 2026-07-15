"""Transparent demonstration tariff calculations."""

from collections.abc import Mapping
from typing import Any

import pandas as pd

from schemas.tariff import TariffCost, TariffRecommendation


def calculate_tariff_cost(
    tariff: Mapping[str, Any] | pd.Series,
    transfer_count: int,
    acquiring_turnover: float,
) -> TariffCost:
    """Calculate full monthly cost for one tariff."""

    monthly_fee = float(tariff["monthly_fee"])
    extra_transfers = max(0, transfer_count - int(tariff["transfer_limit"]))
    transfer_cost = extra_transfers * float(tariff["transfer_commission"])
    acquiring_cost = acquiring_turnover * float(tariff["acquiring_commission"])
    return TariffCost(
        str(tariff["name"]), monthly_fee, transfer_cost, acquiring_cost,
        monthly_fee + transfer_cost + acquiring_cost,
    )


def compare_tariffs(
    tariffs: pd.DataFrame, transfer_count: int, acquiring_turnover: float
) -> pd.DataFrame:
    """Return all tariff costs ordered from cheapest to most expensive."""

    costs = [
        calculate_tariff_cost(row, transfer_count, acquiring_turnover).__dict__
        for _, row in tariffs.iterrows()
    ]
    return pd.DataFrame(costs).sort_values("total").reset_index(drop=True)


def build_tariff_recommendation(
    tariffs: pd.DataFrame,
    current_tariff: str,
    transfer_count: int,
    acquiring_turnover: float,
    forecast_transfer_count: int | None = None,
) -> TariffRecommendation:
    """Recommend the lowest-cost tariff without changing anything automatically."""

    comparison = compare_tariffs(tariffs, transfer_count, acquiring_turnover)
    best = comparison.iloc[0]
    current_rows = comparison[comparison["tariff_name"] == current_tariff]
    if current_rows.empty:
        raise ValueError(f"Тариф «{current_tariff}» не найден")
    current = current_rows.iloc[0]
    tariff_row = tariffs[tariffs["name"] == current_tariff].iloc[0]
    warnings: list[str] = []
    limit = int(tariff_row["transfer_limit"])
    if limit and transfer_count >= limit * 0.8:
        warnings.append(f"Использовано не менее 80% лимита переводов ({transfer_count} из {limit}).")
    if forecast_transfer_count is not None and forecast_transfer_count > limit:
        warnings.append(f"Прогноз ({forecast_transfer_count}) превышает лимит переводов ({limit}).")
    savings = max(0.0, float(current["total"] - best["total"]))
    reason = (
        "При заданном числе переводов и обороте этот вариант имеет минимальную расчетную стоимость."
        if savings > 0
        else "Текущий тариф уже имеет минимальную расчетную стоимость."
    )
    return TariffRecommendation(
        current_tariff,
        str(best["tariff_name"]),
        float(current["total"]),
        float(best["total"]),
        savings,
        reason,
        warnings,
    )
