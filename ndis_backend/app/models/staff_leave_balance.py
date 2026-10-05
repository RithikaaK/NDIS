"""StaffLeaveBalance ORM model."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffLeaveBalance(Base):
    """Leave balance per staff per leave type per period. Lives in per-tenant schema."""

    __tablename__ = "staff_leave_balance"
    __table_args__ = {"schema": "tenant_schema"}

    leave_balance_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    leave_type_id: Mapped[str] = mapped_column(String(50), nullable=False)
    leave_period: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    opening_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    accrued_leave: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    available_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
