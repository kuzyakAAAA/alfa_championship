"""Context-bound financial assistant with an offline mock mode."""

from dataclasses import asdict
from typing import Any

from schemas.analytics import AnalyticsMetrics


DISCLAIMER = "Ответ носит информационный характер и не заменяет бухгалтерскую или налоговую консультацию."
SYSTEM_PROMPT = (
    "Ты финансовый помощник малого бизнеса. Используй только переданные рассчитанные показатели, "
    "не придумывай числа и явно сообщай, когда данных недостаточно."
)


def prepare_ai_context(metrics: AnalyticsMetrics, alerts: list[str]) -> dict[str, Any]:
    """Build a serializable context containing calculated values only."""

    return {"metrics": asdict(metrics), "alerts": alerts}


def answer_question(question: str, context: dict[str, Any], api_key: str = "") -> str:
    """Answer from context; external integration remains an explicit extension point."""

    metrics = context.get("metrics", {})
    alerts = context.get("alerts", [])
    normalized = question.lower()
    if "прибыл" in normalized:
        answer = f"Расчетная прибыль за выбранный период: {metrics.get('profit', 0):,.0f} ₽."
    elif "расход" in normalized:
        answer = f"Расходы за выбранный период: {metrics.get('expenses', 0):,.0f} ₽."
    elif "выруч" in normalized:
        answer = f"Выручка за выбранный период: {metrics.get('revenue', 0):,.0f} ₽."
    elif "риск" in normalized or "аномал" in normalized:
        answer = "Текущие предупреждения: " + ("; ".join(alerts) if alerts else "существенных сигналов не найдено") + "."
    else:
        answer = (
            f"Доступные показатели: выручка {metrics.get('revenue', 0):,.0f} ₽, "
            f"расходы {metrics.get('expenses', 0):,.0f} ₽, прибыль {metrics.get('profit', 0):,.0f} ₽. "
            "Уточните, какой из них разобрать."
        )
    mode = "Mock-режим. " if not api_key else "Локальный прототип ответа. "
    return f"{mode}{answer} {DISCLAIMER}".replace(",", " ")
