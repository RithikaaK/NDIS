"""StaffGoal ORM model — individual development/performance goals per staff member."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffGoal(Base):
    """Development or performance goal for a staff member. Lives in per-tenant schema."""

    __tablename__ = "staff_goal"
    __table_args__ = {"schema": "tenant_schema"}

    goal_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    review_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # optional link to review

    goal_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    goal_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # Training / Compliance / Development
    goal_period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)     # e.g. "Q4 2026"
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    goal_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)     # Not Started / In Progress / Completed
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    set_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)          # user_id of manager who set goal
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
