"""StaffExitProcess ORM model."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffExitProcess(Base):
    """Exit/offboarding records for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_exit_process"
    __table_args__ = {"schema": "tenant_schema"}

    exit_process_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    exit_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    resignation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_working_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notice_period_served: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    exit_interview_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    handover_completed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    agreement_copy_uploaded: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    agreement_file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_revoked_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
