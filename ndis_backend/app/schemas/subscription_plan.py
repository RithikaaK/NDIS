"""Subscription plan schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SubscriptionPlanResponse(BaseModel):
    """Response schema for subscription plan."""
    model_config = ConfigDict(from_attributes=True)

    plan_id: int
    plan_code: str
    plan_name: str
    max_branches: int
    max_users: int
    max_participants: int
    monthly_price: Decimal
    monthly_fee_aud: Optional[Decimal] = None
    annual_fee_aud: Optional[Decimal] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
