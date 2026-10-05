"""TenantContact ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TenantContact(Base):
    """Primary, billing, and operational contact persons for the tenant.
    Lives in the per-tenant schema (tenant_schema placeholder — resolved at request time).
    tenant_id is stored for reference; schema isolation enforces tenant boundary.
    """
    __tablename__ = "tenant_contact"
    __table_args__ = (
        UniqueConstraint("tenant_id", "contact_type", name="UQ_tenant_contact_tenant_type"),
        {"schema": "tenant_schema"},
    )

    contact_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    contact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position_title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
