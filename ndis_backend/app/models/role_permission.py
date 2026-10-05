"""RolePermission ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RolePermission(Base):
    """Mapping of permissions granted to a role.
    Lives in per-tenant schema (tenant_schema placeholder — resolved at request time).
    """
    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="UQ_role_permission_role_perm"),
        {"schema": "tenant_schema"},
    )

    role_permission_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_schema.role.role_id"), nullable=False
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_schema.permission.permission_id"), nullable=False
    )
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="role_permissions")
