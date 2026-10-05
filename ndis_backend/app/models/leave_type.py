"""LeaveType ORM model — master leave type catalogue."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LeaveType(Base):
    """Master leave type catalogue shared across tenants. Lives in ndis_common schema."""

    __tablename__ = "leave_type"
    __table_args__ = {"schema": "ndis_common"}

    leave_type_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    leave_type_name: Mapped[str] = mapped_column(String(50), nullable=False)
    leave_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    paid_leave: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
