"""Transaction normalization and categorization."""

from collections.abc import Iterable
from typing import Any

import pandas as pd

from utils.validators import validate_required_columns


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Продажи": ("заказ", "продаж", "оплата покупателя", "эквайринг"),
    "Реклама": ("реклам", "маркетинг", "директ", "продвижение"),
    "Аренда": ("аренд", "офис", "склад"),
    "Закупки": ("закуп", "поставщик", "товар", "ткан"),
    "Доставка": ("достав", "курьер", "логист"),
    "Налоги": ("налог", "фнс", "взнос"),
    "Зарплаты": ("зарплат", "аванс", "оплата труда"),
    "Подписки": ("подписк", "сервис", "crm", "хостинг"),
    "Банковские комиссии": ("комисси", "обслуживание банка"),
    "Возвраты": ("возврат", "refund"),
}


def categorize_description(description: str, operation_type: str = "") -> str:
    """Categorize an operation using transparent keyword rules."""

    if operation_type == "refund":
        return "Возвраты"
    if operation_type == "commission":
        return "Банковские комиссии"
    text = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Другое"


def clean_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate, normalize and de-duplicate uploaded operations."""

    data = frame.copy()
    data.columns = [str(column).strip().lower() for column in data.columns]
    validate_required_columns(data.columns)
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    data["operation_type"] = data["operation_type"].astype(str).str.strip().str.lower()
    data["description"] = data["description"].fillna("").astype(str).str.strip()
    allowed_types = {"income", "expense", "refund", "commission"}
    invalid = data.loc[~data["operation_type"].isin(allowed_types), "operation_type"].unique()
    if len(invalid):
        raise ValueError(f"Недопустимые типы операций: {', '.join(map(str, invalid))}")
    if data["date"].isna().any():
        raise ValueError("В CSV есть строки с некорректной датой")
    if data["amount"].isna().any() or (data["amount"] < 0).any():
        raise ValueError("В CSV есть строки с некорректной суммой")

    if "category" not in data:
        data["category"] = ""
    if "payment_channel" not in data:
        data["payment_channel"] = "Не указан"
    data["category"] = data["category"].fillna("").astype(str).str.strip()
    inferred = [
        categorize_description(description, operation_type)
        for description, operation_type in zip(
            data["description"], data["operation_type"], strict=False
        )
    ]
    data["category"] = data["category"].where(data["category"].ne(""), inferred)
    data["payment_channel"] = data["payment_channel"].fillna("Не указан").astype(str)
    return data.drop_duplicates().sort_values("date").reset_index(drop=True)


def prepare_transaction_records(
    frame: pd.DataFrame, company_id: int, is_demo: bool = False
) -> list[dict[str, Any]]:
    """Convert normalized data to repository-ready dictionaries."""

    data = clean_transactions(frame)
    return [
        {
            "company_id": company_id,
            "operation_date": row.date.date(),
            "amount": float(row.amount),
            "operation_type": row.operation_type,
            "category": row.category,
            "description": row.description,
            "payment_channel": row.payment_channel,
            "is_demo": is_demo,
        }
        for row in data.itertuples(index=False)
    ]


class TransactionService:
    """Compatibility facade for transaction processing."""

    @staticmethod
    def process_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
        return clean_transactions(frame)

    @staticmethod
    def prepare_records(
        frame: pd.DataFrame, company_id: int, is_demo: bool = False
    ) -> list[dict[str, Any]]:
        return prepare_transaction_records(frame, company_id, is_demo)
