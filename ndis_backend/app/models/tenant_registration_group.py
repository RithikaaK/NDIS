"""TenantRegistrationGroup ORM model."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TenantRegistrationGroup(Base):
    """NDIS Registration Groups approved for the tenant (Registered providers).
    Lives in the per-tenant schema (tenant_schema placeholder — resolved at request time).
    tenant_id is stored for reference; schema isolation enforces tenant boundary.
    """
    __tablename__ = "tenant_registration_group"
    __table_args__ = (
        UniqueConstraint("tenant_id", "registration_group_code", name="UQ_tenant_reg_group_code"),
        {"schema": "tenant_schema"},
    )

    tenant_reg_group_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    registration_group_code: Mapped[str] = mapped_column(String(20), nullable=False)
    registration_group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
