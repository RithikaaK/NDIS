"""StaffTimesheetHeader ORM model."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffTimesheetHeader(Base):
    """Timesheet header (one per work day per staff). Lives in per-tenant schema."""

    __tablename__ = "staff_timesheet_header"
    __table_args__ = {"schema": "tenant_schema"}

    timesheet_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    work_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    timesheet_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    submitted_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approval_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    total_overtime_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
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
