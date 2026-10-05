"""StaffProbation ORM model."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffProbation(Base):
    """Probation tracking for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_probation"
    __table_args__ = {"schema": "tenant_schema"}

    probation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    probation_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    probation_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    probation_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    probation_review_notes: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    probation_extension_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confirmed_as_permanent: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
