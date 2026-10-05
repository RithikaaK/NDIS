"""StaffContract ORM model."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffContract(Base):
    """Contract records for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_contract"
    __table_args__ = {"schema": "tenant_schema"}

    contract_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    contract_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    contract_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    contract_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    contract_uploaded: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contract_file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contract_renewal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notice_period_timeline: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    schads_applicable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
