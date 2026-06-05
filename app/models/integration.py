"""
Tax God - Integration Credential Model
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"

    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (PrimaryKeyConstraint("user_id", "provider"),)

    def __repr__(self) -> str:
        return f"<IntegrationCredential {self.user_id}:{self.provider}>"
