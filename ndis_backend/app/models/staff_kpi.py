"""StaffKpi ORM model — individual KPI line items within a performance review."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffKpi(Base):
    """KPI line item linked to a performance review. Lives in per-tenant schema."""

    __tablename__ = "staff_kpi"
    __table_args__ = {"schema": "tenant_schema"}

    kpi_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    review_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    kpi_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    kpi_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # e.g. Punctuality, Care Quality
    target_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    actual_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)   # 0–5
    weight_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # contribution %
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)          # e.g. "Q3 2026"

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
