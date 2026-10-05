"""UserRole ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(Base):
    """Mapping table for roles assigned to users.
    Lives in per-tenant schema (tenant_schema placeholder — resolved at request time).

    user_id references ndis_common.app_user — stored as a plain string (logical reference,
    no DB FK constraint) because cross-schema FKs between ndis_common and tenant_schema
    are not enforced at the database level.
    """
    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="UQ_user_role_user_role"),
        {"schema": "tenant_schema"},
    )

    user_role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Logical reference to ndis_common.app_user — no FK constraint
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_schema.role.role_id"), nullable=False
    )
    assigned_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships — only within tenant_schema
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    # Note: user relationship removed — AppUser is in ndis_common (cross-schema)
