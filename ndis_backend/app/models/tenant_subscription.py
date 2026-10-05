"""TenantSubscription ORM model."""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import DateTime, Date, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TenantSubscription(Base):
    """Tenant subscription linkage to SubscriptionPlan and billing cycle history.
    Lives in ndis_common schema.
    """
    __tablename__ = "tenant_subscription"
    __table_args__ = {"schema": "ndis_common"}

    subscription_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ndis_common.tenant.tenant_id"), nullable=False
    )
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ndis_common.subscription_plan.plan_id"), nullable=False
    )
    billing_cycle: Mapped[str] = mapped_column(String(10), default="Monthly", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscriptions")
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan", back_populates="subscriptions")
