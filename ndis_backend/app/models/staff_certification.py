"""StaffCertification ORM model — maps staff to certifications."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffCertification(Base):
    """Certification records held by a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_certification"
    __table_args__ = {"schema": "tenant_schema"}

    staff_certification_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    certification_id: Mapped[str] = mapped_column(String(20), nullable=False)
    certification_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    issuing_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    document_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_uploaded: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    verification_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
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
