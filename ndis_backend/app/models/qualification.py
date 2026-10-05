"""Qualification ORM model — master list of qualifications (common, no tenant)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Qualification(Base):
    """Master qualification catalogue shared across tenants. Lives in ndis_common schema."""

    __tablename__ = "qualification"
    __table_args__ = {"schema": "ndis_common"}

    qualification_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    qualification_type: Mapped[str] = mapped_column(String(150), nullable=False)
    qualification_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    qualification_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
