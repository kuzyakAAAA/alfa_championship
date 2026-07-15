"""SQLAlchemy setup and session helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DATABASE_URL, DATA_DIR


class Base(DeclarativeBase):
    """Base class for ORM models."""


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session and always close it afterwards."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create the local database tables."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
