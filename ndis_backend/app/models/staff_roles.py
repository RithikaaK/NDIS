"""StaffRoles ORM model — staff job roles within the organisation."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffRoles(Base):
    """Assigned job roles for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_roles"
    __table_args__ = {"schema": "tenant_schema"}

    staff_role_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    role_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    role_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    role_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
