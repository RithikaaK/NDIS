"""TenantDocument ORM model."""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TenantDocument(Base):
    """Organisation-level files, registration certificates, and compliance policies.
    Lives in the per-tenant schema (tenant_schema placeholder — resolved at request time).
    tenant_id is stored for reference; schema isolation enforces tenant boundary.
    """
    __tablename__ = "tenant_document"
    __table_args__ = {"schema": "tenant_schema"}

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    document_category: Mapped[str] = mapped_column(String(100), nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_kb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linked_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String(50), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
