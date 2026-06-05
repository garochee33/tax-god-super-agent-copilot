"""
Tax God - Invoice Model
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    client_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clients.id"), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    items: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        return f"<Invoice {self.invoice_number}>"
