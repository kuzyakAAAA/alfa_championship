"""Database access for transactions."""

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models import Transaction


def save_transaction(session: Session, values: dict) -> Transaction:
    transaction = Transaction(**values)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def save_transactions(session: Session, values: list[dict]) -> list[Transaction]:
    transactions = [Transaction(**item) for item in values]
    session.add_all(transactions)
    session.commit()
    return transactions


def get_by_company(session: Session, company_id: int) -> list[Transaction]:
    statement = select(Transaction).where(Transaction.company_id == company_id).order_by(Transaction.operation_date)
    return list(session.scalars(statement))


def get_by_period(session: Session, company_id: int, start: date, end: date) -> list[Transaction]:
    statement = select(Transaction).where(
        Transaction.company_id == company_id,
        Transaction.operation_date.between(start, end),
    )
    return list(session.scalars(statement))


def delete_demo_transactions(session: Session, company_id: int) -> int:
    """Delete only explicitly marked demo records for one company."""

    result = session.execute(
        delete(Transaction).where(Transaction.company_id == company_id, Transaction.is_demo.is_(True))
    )
    session.commit()
    return int(result.rowcount or 0)
