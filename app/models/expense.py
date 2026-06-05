"""
Tax God - Expense Model
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExpenseCategory(str, Enum):
    OFFICE = "office"
    TRAVEL = "travel"
    MEALS = "meals"
    AUTO = "auto"
    INSURANCE = "insurance"
    PROFESSIONAL_SERVICES = "professional_services"
    UTILITIES = "utilities"
    SOFTWARE = "software"
    MARKETING = "marketing"
    RENT = "rent"
    PAYROLL = "payroll"
    TAXES = "taxes"
    OTHER = "other"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    business_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vendor: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tax_deductible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    account_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Expense {self.vendor} ${self.amount}>"
