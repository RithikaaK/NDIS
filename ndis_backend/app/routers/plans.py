"""Subscription Plans router."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_get, cache_set
from app.database import get_db
from app.models import SubscriptionPlan
from app.schemas import SubscriptionPlanResponse

router = APIRouter(tags=["Subscription Plans"])

TTL_PLANS = 600


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_subscription_plans(
    db: AsyncSession = Depends(get_db),
) -> List[SubscriptionPlanResponse]:
    """Public endpoint: returns all active subscription plans."""
    key = "plans:all"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    plans = (await db.scalars(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True)  # noqa: E712
        .order_by(SubscriptionPlan.plan_id)
    )).all()

    result = [SubscriptionPlanResponse.model_validate(p).model_dump(mode="json") for p in plans]
    await cache_set(key, result, ttl=TTL_PLANS)
    return result
