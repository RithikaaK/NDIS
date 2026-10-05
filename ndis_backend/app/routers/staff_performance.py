"""Staff Performance router — reviews, KPIs, and goals."""
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models.staff_performance_review import StaffPerformanceReview
from app.models.staff_kpi import StaffKpi
from app.models.staff_goal import StaffGoal
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_performance import (
    StaffPerformanceReviewCreate, StaffPerformanceReviewUpdate, StaffPerformanceReviewResponse,
    StaffKpiCreate, StaffKpiUpdate, StaffKpiResponse,
    StaffGoalCreate, StaffGoalUpdate, StaffGoalResponse,
)

router = APIRouter(tags=["Staff — Performance"])

BASE = "/tenant/{tenant_id}/staff"


def _uid() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE REVIEWS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/performance-reviews", response_model=List[StaffPerformanceReviewResponse])
async def list_performance_reviews(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(
        select(StaffPerformanceReview).where(
            StaffPerformanceReview.staff_id == staff_id,
            StaffPerformanceReview.tenant_id == tenant_id,
            StaffPerformanceReview.is_deleted == False,  # noqa: E712
        ).order_by(StaffPerformanceReview.created_at.desc())
    )).all()
    return [StaffPerformanceReviewResponse.model_validate(r) for r in rows]


@router.post(
    BASE + "/{staff_id}/performance-reviews",
    response_model=StaffPerformanceReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_review(
    tenant_id: int,
    staff_id: str,
    payload: StaffPerformanceReviewCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = StaffPerformanceReview(
        review_id=_uid(),
        tenant_id=tenant_id,
        staff_id=staff_id,
        **payload.model_dump(),
        created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_performance_review", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffPerformanceReviewResponse.model_validate(record)


@router.get(
    BASE + "/{staff_id}/performance-reviews/{review_id}",
    response_model=StaffPerformanceReviewResponse,
)
async def get_performance_review(
    tenant_id: int,
    staff_id: str,
    review_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    record = await db.scalar(
        select(StaffPerformanceReview).where(
            StaffPerformanceReview.review_id == review_id,
            StaffPerformanceReview.staff_id == staff_id,
            StaffPerformanceReview.is_deleted == False,  # noqa: E712
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="Performance review not found")
    return StaffPerformanceReviewResponse.model_validate(record)


@router.patch(
    BASE + "/{staff_id}/performance-reviews/{review_id}",
    response_model=StaffPerformanceReviewResponse,
)
async def update_performance_review(
    tenant_id: int,
    staff_id: str,
    review_id: str,
    payload: StaffPerformanceReviewUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = await db.scalar(
        select(StaffPerformanceReview).where(
            StaffPerformanceReview.review_id == review_id,
            StaffPerformanceReview.staff_id == staff_id,
            StaffPerformanceReview.is_deleted == False,  # noqa: E712
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="Performance review not found")
    old = {"review_status": record.review_status, "overall_score": str(record.overall_score)}
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(
        db, current_user.get("user_id"), "UPDATE", "staff_performance_review", review_id,
        old_values=old, new_values=payload.model_dump(exclude_unset=True), request=request,
    )
    await db.commit()
    await db.refresh(record)
    return StaffPerformanceReviewResponse.model_validate(record)


@router.delete(
    BASE + "/{staff_id}/performance-reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_performance_review(
    tenant_id: int,
    staff_id: str,
    review_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = await db.scalar(
        select(StaffPerformanceReview).where(
            StaffPerformanceReview.review_id == review_id,
            StaffPerformanceReview.staff_id == staff_id,
            StaffPerformanceReview.is_deleted == False,  # noqa: E712
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="Performance review not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_performance_review", review_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# KPIs
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/kpis", response_model=List[StaffKpiResponse])
async def list_kpis(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(
        select(StaffKpi).where(
            StaffKpi.staff_id == staff_id,
            StaffKpi.tenant_id == tenant_id,
            StaffKpi.is_deleted == False,  # noqa: E712
        ).order_by(StaffKpi.created_at.desc())
    )).all()
    return [StaffKpiResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/kpis", response_model=StaffKpiResponse, status_code=status.HTTP_201_CREATED)
async def create_kpi(
    tenant_id: int,
    staff_id: str,
    payload: StaffKpiCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = StaffKpi(
        kpi_id=_uid(),
        tenant_id=tenant_id,
        staff_id=staff_id,
        **payload.model_dump(),
        created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_kpi", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffKpiResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/kpis/{kpi_id}", response_model=StaffKpiResponse)
async def update_kpi(
    tenant_id: int,
    staff_id: str,
    kpi_id: str,
    payload: StaffKpiUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = await db.scalar(
        select(StaffKpi).where(
            StaffKpi.kpi_id == kpi_id,
            StaffKpi.staff_id == staff_id,
            StaffKpi.is_deleted == False,  # noqa: E712
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="KPI not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_kpi", kpi_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffKpiResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/kpis/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kpi(
    tenant_id: int,
    staff_id: str,
    kpi_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = await db.scalar(
        select(StaffKpi).where(
            StaffKpi.kpi_id == kpi_id,
            StaffKpi.staff_id == staff_id,
            StaffKpi.is_deleted == False,  # noqa: E712
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="KPI not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_kpi", kpi_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# GOALS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/goals", response_model=List[StaffGoalResponse])
async def list_goals(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(
        select(StaffGoal).where(
            StaffGoal.staff_id == staff_id,
            StaffGoal.tenant_id == tenant_id,
            StaffGoal.is_deleted == False,  # noqa: E712
        ).order_by(StaffGoal.due_date.asc())
    )).all()
    return [StaffGoalResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/goals", response_model=StaffGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    tenant_id: int,
    staff_id: str,
    payload: StaffGoalCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = StaffGoal(
        goal_id=_uid(),
        tenant_id=tenant_id,
        staff_id=staff_id,
        **payload.model_dump(),
        created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_goal", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffGoalResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/goals/{goal_id}", response_model=StaffGoalResponse)
async def update_goal(
    tenant_id: int,
    staff_id: str,
    goal_id: str,
    payload: StaffGoalUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = await db.scalar(
        select(StaffGoal).where(
            StaffGoal.goal_id == goal_id,
            StaffGoal.staff_id == staff_id,
            StaffGoal.is_deleted == False,  # noqa: E712
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="Goal not found")
    old = {"goal_status": record.goal_status}
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(
        db, current_user.get("user_id"), "UPDATE", "staff_goal", goal_id,
        old_values=old, new_values=payload.model_dump(exclude_unset=True), request=request,
    )
    await db.commit()
    await db.refresh(record)
    return StaffGoalResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    tenant_id: int,
    staff_id: str,
    goal_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:performance")
    record = await db.scalar(
        select(StaffGoal).where(
            StaffGoal.goal_id == goal_id,
            StaffGoal.staff_id == staff_id,
            StaffGoal.is_deleted == False,  # noqa: E712
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="Goal not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_goal", goal_id, request=request)
    await db.commit()
