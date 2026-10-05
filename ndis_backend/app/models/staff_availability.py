"""StaffAvailability ORM model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffAvailability(Base):
    """Availability records for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_availability"
    __table_args__ = {"schema": "tenant_schema"}

    availability_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    availability_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    availability_effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    availability_effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    availability_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    current_shift_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    available_for_overtime: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    available_for_on_call: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    availability_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
