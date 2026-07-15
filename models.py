"""Database models for companies, operations and recommendations."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Company(Base):
    """A business using the prototype."""

    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="forecasts")


class Alert(Base):
    """Detected financial warning."""

    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(60))
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="alerts")
