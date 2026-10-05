"""StaffLeaveRequest ORM model."""
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffLeaveRequest(Base):
    """Leave request header for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_leave_request"
    __table_args__ = {"schema": "tenant_schema"}

    leave_request_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    leave_type_id: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_for_leave: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supporting_document_uploaded: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    submitted_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    submitted_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    leave_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    approval_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    decline_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backfill_required: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    backfill_staff_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    participants_notified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
