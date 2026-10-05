"""TenantAddress ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TenantAddress(Base):
    """Registered, mailing, and physical business addresses of the tenant.
    Lives in the per-tenant schema (tenant_schema placeholder — resolved at request time).
    tenant_id is stored for reference; schema isolation enforces tenant boundary.
    """
    __tablename__ = "tenant_address"
    __table_args__ = {"schema": "tenant_schema"}

    address_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    address_type: Mapped[str] = mapped_column(String(50), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    suburb: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    postcode: Mapped[str] = mapped_column(String(10), nullable=False)
    country_code: Mapped[str] = mapped_column(String(3), default="AUS", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
