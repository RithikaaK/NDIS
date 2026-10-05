"""StaffLeaveRequestDate ORM model — individual date entries for a leave request."""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffLeaveRequestDate(Base):
    """Date-level detail rows for a staff leave request. Lives in per-tenant schema."""

    __tablename__ = "staff_leave_request_date"
    __table_args__ = {"schema": "tenant_schema"}

    leave_request_date_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    leave_request_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    leave_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    leave_duration: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    leave_start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    leave_end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    leave_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
