"""StaffIdentification ORM model."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffIdentification(Base):
    """Identity documents for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_identification"
    __table_args__ = {"schema": "tenant_schema"}

    staff_iden_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    identification_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    identification_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    document_attached: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    verified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verified_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
