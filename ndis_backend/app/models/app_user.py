"""AppUser ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AppUser(Base):
    """System users with identity credentials. Lives in ndis_common schema.

    branch_id is stored as a plain integer (logical reference) — no FK constraint
    because Branch lives in the per-tenant schema.  Access branch data via the
    tenant-scoped session (get_tenant_db).
    """
    __tablename__ = "app_user"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="UQ_app_user_tenant_email"),
        {"schema": "ndis_common"},
    )

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ndis_common.tenant.tenant_id"), nullable=False
    )
    # Logical reference to tenant_schema.branch — no FK constraint (cross-schema)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    is_tenant_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )

    # Relationships — only within ndis_common
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    # Note: branch, user_roles, cross_branch_accesses are in the per-tenant schema.
    # Query them via the tenant-scoped session (get_tenant_db) using user_id directly.
