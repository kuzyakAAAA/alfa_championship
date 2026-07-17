"""Database models for companies, operations and financial planning."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utc_now() -> datetime:
    """Return a naive UTC timestamp compatible with existing SQLite columns."""

    return datetime.now(UTC).replace(tzinfo=None)


class Company(Base):
    """A business using the prototype."""

    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="company")
    forecasts: Mapped[list["Forecast"]] = relationship(back_populates="company")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="company")


class Transaction(Base):
    """Normalized financial operation."""

    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    operation_date: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    operation_type: Mapped[str] = mapped_column(String(30), index=True)
    category: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(500))
    payment_channel: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_demo: Mapped[bool] = mapped_column(default=False)
    company: Mapped[Company] = relationship(back_populates="transactions")


class Tariff(Base):
    """Demonstration banking tariff."""

    __tablename__ = "tariffs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    monthly_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    transfer_limit: Mapped[int]
    transfer_commission: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    acquiring_commission: Mapped[Decimal] = mapped_column(Numeric(8, 5))
    description: Mapped[str] = mapped_column(Text)


class Forecast(Base):
    """Saved revenue forecast point."""

    __tablename__ = "forecasts"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    forecast_date: Mapped[date] = mapped_column(Date)
    scenario: Mapped[str] = mapped_column(String(30))
    value: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    company: Mapped[Company] = relationship(back_populates="forecasts")


class Alert(Base):
    """Detected financial warning."""

    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(60))
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    company: Mapped[Company] = relationship(back_populates="alerts")


class CalendarProfile(Base):
    """Persisted settings for one local payment-calendar data source."""

    __tablename__ = "calendar_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_key: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    balance_mode: Mapped[str] = mapped_column(String(20), default="calculated")
    manual_balance: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    scenario: Mapped[str] = mapped_column(String(20), default="base")
    horizon_days: Mapped[int] = mapped_column(default=90)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
    cashflows: Mapped[list["PlannedCashflow"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class PlannedCashflow(Base):
    """A manually planned payment or expected receipt."""

    __tablename__ = "planned_cashflows"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("calendar_profiles.id"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    due_date: Mapped[date] = mapped_column(Date, index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recurrence: Mapped[str] = mapped_column(String(20), default="once")
    recurrence_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
    profile: Mapped[CalendarProfile] = relationship(back_populates="cashflows")
