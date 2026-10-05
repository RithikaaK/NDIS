"""TenantServiceState ORM model."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TenantServiceState(Base):
    """Operational states and territories where the tenant delivers NDIS services.
    Lives in the per-tenant schema (tenant_schema placeholder — resolved at request time).
    tenant_id is stored for reference; schema isolation enforces tenant boundary.
    """
    __tablename__ = "tenant_service_state"
    __table_args__ = (
        UniqueConstraint("tenant_id", "state_code", name="UQ_tenant_service_state_tenant_state"),
        {"schema": "tenant_schema"},
    )

    service_state_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
