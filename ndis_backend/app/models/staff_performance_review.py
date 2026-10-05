"""StaffPerformanceReview ORM model — periodic performance review record."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffPerformanceReview(Base):
    """One review cycle entry per staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_performance_review"
    __table_args__ = {"schema": "tenant_schema"}

    review_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    review_period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)   # e.g. "Q3 2026"
    review_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)     # Annual / Quarterly / Probation
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)     # user_id of reviewer

    # Aggregate scores (stored as DECIMAL 3,2 — range 0.00–5.00)
    overall_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    punctuality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    care_quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    compliance_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    communication_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    teamwork_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)

    reviewer_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    staff_self_assessment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)   # Draft / Completed / Acknowledged

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
