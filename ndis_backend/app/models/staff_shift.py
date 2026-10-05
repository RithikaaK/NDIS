"""StaffShift ORM model — backs Shift Scheduling / Staff-to-Shift Assignment /
Recurring Roster Management (features 4.3–4.5). Lives in per-tenant schema."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffShift(Base):
    """A single rostered shift for a staff member.

    day_of_week: 0=Mon .. 6=Sun, matching the frontend's roster calendar.
    A recurring shift (is_recurring=True) repeats weekly on day_of_week
    between recurring_from/recurring_to (recurring_to null = ongoing).
    """

    __tablename__ = "staff_shift"
    __table_args__ = {"schema": "tenant_schema"}

    shift_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    shift_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    start_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    end_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    shift_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default="Confirmed")

    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurring_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    recurring_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

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
