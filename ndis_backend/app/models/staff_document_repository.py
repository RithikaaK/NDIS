"""StaffDocumentRepository ORM model."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffDocumentRepository(Base):
    """Document storage records for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_document_repository"
    __table_args__ = {"schema": "tenant_schema"}

    document_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    document_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    document_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_format: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    document_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    upload_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    document_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    expiry_alert_days: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
