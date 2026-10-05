"""EmploymentInformation ORM model."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmploymentInformation(Base):
    """Employment details for a staff member. Lives in per-tenant schema."""

    __tablename__ = "employment_information"
    __table_args__ = {"schema": "tenant_schema"}

    employment_info_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    employment_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    pay_level: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    pay_point: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    position_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contracted_hours_per_week: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    reporting_manager_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employment_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employment_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
