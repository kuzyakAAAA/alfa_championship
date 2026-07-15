"""Simple reproducible revenue forecasting."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from schemas.forecast import ForecastPoint, ForecastResult, ForecastScenario


def prepare_time_series(frame: pd.DataFrame, frequency: str = "MS") -> pd.Series:
    """Build a regular revenue time series."""

    income = frame[frame["operation_type"] == "income"].copy()
    if income.empty:
        return pd.Series(dtype=float)
    income["date"] = pd.to_datetime(income["date"])
    return income.set_index("date")["amount"].resample(frequency).sum().astype(float)


def build_revenue_forecast(frame: pd.DataFrame, periods: int = 3) -> ForecastResult:
    """Forecast monthly revenue with linear regression and fixed scenarios."""

    series = prepare_time_series(frame)
    if len(series) < 3:
        return ForecastResult([], False, "Для прогноза нужны данные минимум за три месяца.")
    x = np.arange(len(series), dtype=float).reshape(-1, 1)
    model = LinearRegression().fit(x, series.to_numpy())
    future_x = np.arange(len(series), len(series) + periods, dtype=float).reshape(-1, 1)
    base_values = np.maximum(model.predict(future_x), 0.0)
    dates = pd.date_range(series.index[-1] + pd.offsets.MonthBegin(1), periods=periods, freq="MS")
    factors = {"Пессимистичный": 0.85, "Базовый": 1.0, "Оптимистичный": 1.15}
    scenarios = [
        ForecastScenario(
            name,
            [ForecastPoint(point.date(), float(value * factor)) for point, value in zip(dates, base_values, strict=False)],
        )
        for name, factor in factors.items()
    ]
    return ForecastResult(
        scenarios,
        True,
        "Прогноз основан на линейном тренде; сезонность и внешние факторы не учитываются.",
    )
