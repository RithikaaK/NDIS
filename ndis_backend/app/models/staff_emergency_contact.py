"""StaffEmergencyContact ORM model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffEmergencyContact(Base):
    """Emergency contact records for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_emergency_contact"
    __table_args__ = {"schema": "tenant_schema"}

    emergency_contact_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    middle_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    relationship_with_staff: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    street_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    area: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    post_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_contact_no: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    secondary_contact_no: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    primary_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    secondary_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_primary_emerg_cntact: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
