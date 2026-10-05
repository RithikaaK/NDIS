"""StaffPreferences ORM model."""
from datetime import datetime, time
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffPreferences(Base):
    """Work preferences for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_preferences"
    __table_args__ = {"schema": "tenant_schema"}

    staff_pref_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    preferred_shift_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    willing_weekend_work: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    willing_public_holiday_work: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    willing_sleepover_shift: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    willing_active_overnight: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    vehicle_available: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    willing_to_travel: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    travel_limit_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    travel_radius_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preferred_contact_time_from: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    preferred_contact_time_to: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    preferred_participant_gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
