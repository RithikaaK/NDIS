"""AuditLog ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """Immutable audit trail of state changes and administrative operations.
    Lives in per-tenant schema (tenant_schema placeholder — resolved at request time).
    No tenant_id column: physical schema isolation guarantees tenant separation.
    user_id is a logical reference to ndis_common.app_user (no FK constraint).
    """
    __tablename__ = "audit_log"
    __table_args__ = {"schema": "tenant_schema"}

    audit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Logical reference to ndis_common.app_user — no FK constraint
    user_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    old_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
