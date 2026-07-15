"""Database access and initial seeding for demo tariffs."""

from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import DATA_DIR
from models import Tariff


def get_all(session: Session) -> list[Tariff]:
    return list(session.scalars(select(Tariff).order_by(Tariff.monthly_fee)))


def get_by_id(session: Session, tariff_id: int) -> Tariff | None:
    return session.get(Tariff, tariff_id)


def find_by_name(session: Session, name: str) -> Tariff | None:
    return session.scalar(select(Tariff).where(Tariff.name == name))


def seed_demo_tariffs(session: Session, csv_path: str | Path | None = None) -> int:
    """Seed tariffs once from the bundled demonstration file."""

    if session.scalar(select(Tariff.id).limit(1)) is not None:
        return 0
    frame = pd.read_csv(csv_path or DATA_DIR / "tariffs.csv")
    records = [Tariff(**row) for row in frame.to_dict(orient="records")]
    session.add_all(records)
    session.commit()
    return len(records)
