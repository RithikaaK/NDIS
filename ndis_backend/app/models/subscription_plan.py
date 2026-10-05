"""SubscriptionPlan ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SubscriptionPlan(Base):
    """SaaS Subscription Plan available to tenants. Lives in ndis_common schema."""
    __tablename__ = "subscription_plan"
    __table_args__ = {"schema": "ndis_common"}

    plan_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    plan_name: Mapped[str] = mapped_column(String(150), nullable=False)
    max_branches: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_users: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    monthly_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    monthly_fee_aud: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    annual_fee_aud: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )

    # Relationships — both ndis_common tables
    subscriptions: Mapped[list["TenantSubscription"]] = relationship(
        "TenantSubscription", back_populates="plan"
    )
