"""StaffPersonalInfo ORM model."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffPersonalInfo(Base):
    """Personal details for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_personal_info"
    __table_args__ = {"schema": "tenant_schema"}

    personal_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    language_spoken: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    permanent_street_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    permanent_area: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    permanent_city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    permanent_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    permanent_post_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    permanent_country_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    same_as_permanent_address: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    residential_street_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    residential_area: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    residential_city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    residential_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    residential_post_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    residential_country_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
