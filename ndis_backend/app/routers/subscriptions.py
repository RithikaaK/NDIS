"""Tenant Subscription router — view and change plan."""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db, get_tenant_session
from app.models import SubscriptionPlan, TenantSubscription
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import MessageResponse

router = APIRouter(tags=["Subscription"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subscription_id: int
    plan_id: int
    plan_code: str
    plan_name: str
    billing_cycle: str
    start_date: date
    end_date: Optional[date] = None
    status: str
    max_branches: int
    max_users: int
    max_participants: int
    monthly_price: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_orm_with_plan(cls, sub: TenantSubscription) -> "SubscriptionResponse":
        plan = sub.plan
        return cls(
            subscription_id=sub.subscription_id,
            plan_id=sub.plan_id,
            plan_code=plan.plan_code,
            plan_name=plan.plan_name,
            billing_cycle=sub.billing_cycle,
            start_date=sub.start_date,
            end_date=sub.end_date,
            status=sub.status,
            max_branches=plan.max_branches,
            max_users=plan.max_users,
            max_participants=plan.max_participants,
            monthly_price=float(plan.monthly_price),
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )


class SubscriptionPlanItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_id: int
    plan_code: str
    plan_name: str
    max_branches: int
    max_users: int
    max_participants: int
    monthly_price: float
    is_active: bool


class SubscriptionChangeRequest(BaseModel):
    plan_code: str = Field(..., description="Target plan code (BASIC, PROFESSIONAL, ENTERPRISE)")
    billing_cycle: str = Field("Monthly", pattern=r"^(Monthly|Annual)$")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/tenant/{tenant_id}/subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Return the tenant's current active subscription with plan details."""
    verify_tenant_access(tenant_id, current_user)

    sub = await db.scalar(
        select(TenantSubscription)
        .where(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status == "Active",
        )
        .options(selectinload(TenantSubscription.plan))
        .order_by(TenantSubscription.subscription_id.desc())
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found for this tenant",
        )
    return SubscriptionResponse.from_orm_with_plan(sub)


@router.get("/tenant/{tenant_id}/subscription/plans", response_model=List[SubscriptionPlanItem])
async def list_available_plans(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[SubscriptionPlanItem]:
    """Return all available subscription plans the tenant can upgrade/downgrade to."""
    verify_tenant_access(tenant_id, current_user)

    plans = (await db.scalars(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True)  # noqa: E712
        .order_by(SubscriptionPlan.monthly_price)
    )).all()
    return [
        SubscriptionPlanItem(
            plan_id=p.plan_id,
            plan_code=p.plan_code,
            plan_name=p.plan_name,
            max_branches=p.max_branches,
            max_users=p.max_users,
            max_participants=p.max_participants,
            monthly_price=float(p.monthly_price),
            is_active=p.is_active,
        )
        for p in plans
    ]


@router.put("/tenant/{tenant_id}/subscription", response_model=SubscriptionResponse)
async def change_subscription_plan(
    tenant_id: int,
    payload: SubscriptionChangeRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> SubscriptionResponse:
    """Change the tenant's subscription plan. Closes the current active sub and opens a new one."""
    verify_tenant_access(tenant_id, current_user)

    # Lookup target plan
    target_plan = await db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.plan_code == payload.plan_code.upper(),
            SubscriptionPlan.is_active == True,  # noqa: E712
        )
    )
    if not target_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{payload.plan_code}' not found or inactive",
        )

    # Close current subscription
    current_sub = await db.scalar(
        select(TenantSubscription)
        .where(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status == "Active",
        )
        .options(selectinload(TenantSubscription.plan))
    )
    today = date.today()
    old_plan_code = None
    if current_sub:
        if current_sub.plan_id == target_plan.plan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant is already on the '{payload.plan_code}' plan",
            )
        old_plan_code = current_sub.plan.plan_code if current_sub.plan else None
        current_sub.status = "Cancelled"
        current_sub.end_date = today

    # Create new subscription
    new_sub = TenantSubscription(
        tenant_id=tenant_id,
        plan_id=target_plan.plan_id,
        billing_cycle=payload.billing_cycle,
        start_date=today,
        status="Active",
    )
    db.add(new_sub)
    await db.flush()

    await log_audit(
        db=tenant_db,
        user_id=current_user["user_id"],
        action="CHANGE_PLAN",
        table_name="tenant_subscription",
        record_id=str(new_sub.subscription_id),
        old_values={"plan_code": old_plan_code},
        new_values={"plan_code": target_plan.plan_code, "billing_cycle": payload.billing_cycle},
        request=request,
    )
    await db.commit()
    await tenant_db.commit()

    # Re-fetch with plan loaded for response
    new_sub = await db.scalar(
        select(TenantSubscription)
        .where(TenantSubscription.subscription_id == new_sub.subscription_id)
        .options(selectinload(TenantSubscription.plan))
    )
    return SubscriptionResponse.from_orm_with_plan(new_sub)
