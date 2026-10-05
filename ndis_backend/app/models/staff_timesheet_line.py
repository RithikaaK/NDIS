"""StaffTimesheetLine ORM model — individual shift entries under a timesheet header."""
from datetime import datetime, time
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffTimesheetLine(Base):
    """Individual shift line items on a timesheet. Lives in per-tenant schema."""

    __tablename__ = "staff_timesheet_line"
    __table_args__ = {"schema": "tenant_schema"}

    timesheet_line_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timesheet_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    shift_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ndis_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    scheduled_start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    scheduled_end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    actual_clock_on_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    actual_clock_off_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    break_taken: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    break_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    care_note_submitted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    line_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
