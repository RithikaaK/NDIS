"""Certification ORM model — master certification catalogue."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Certification(Base):
    """Master certification catalogue shared across tenants. Lives in ndis_common schema."""

    __tablename__ = "certification"
    __table_args__ = {"schema": "ndis_common"}

    certification_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    certification_name: Mapped[str] = mapped_column(String(150), nullable=False)
    certification_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    certification_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expiry_applicability: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    validity_period_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    renewal_required: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
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
