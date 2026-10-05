"""StaffContactInfo ORM model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffContactInfo(Base):
    """Contact details for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_contact_info"
    __table_args__ = {"schema": "tenant_schema"}

    staff_contact_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    primary_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    secondary_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_contact_no: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    secondary_contact_no: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
