"""Tenant ORM model."""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tenant(Base):
    """Core Tenant organisation model. Lives in ndis_common schema (central/unique schema)."""
    __tablename__ = "tenant"
    __table_args__ = {"schema": "ndis_common"}

    tenant_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    # System-generated schema name for this tenant's per-tenant schema.
    # e.g. "tenant_sunshi_001" — never user-provided, always derived from tenant_code.
    schema_name: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    organisation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trading_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    abn: Mapped[Optional[str]] = mapped_column(String(11), unique=True, nullable=True)
    acn: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    is_registered_provider: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ndis_registration_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    registration_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    provider_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    organisation_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    primary_email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    primary_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="Australia/Sydney", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Active", nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )

    # Relationships — only to ndis_common tables that remain in unique schema
    subscriptions: Mapped[list["TenantSubscription"]] = relationship(
        "TenantSubscription", back_populates="tenant", cascade="all, delete-orphan"
    )
    users: Mapped[list["AppUser"]] = relationship(
        "AppUser", back_populates="tenant", cascade="all, delete-orphan"
    )
    # Note: contacts, addresses, service_states, registration_groups, documents,
    # branches, programs, roles, and config all live in the per-tenant schema.
    # Access them via the tenant-scoped session (get_tenant_session).
