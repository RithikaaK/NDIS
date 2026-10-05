"""Staff Shifts router — features 4.3 Shift Scheduling, 4.4 Staff-to-Shift
Assignment, 4.5 Recurring Roster Management.

Mirrors the staff_availability.py router's ORM-based pattern. Uses the
pre-existing schedules:view/create/edit/delete permissions (already seeded
for every role in roles.py) rather than introducing a new permission set.
"""
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models.staff_shift import StaffShift
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_shift import StaffShiftCreate, StaffShiftUpdate, StaffShiftResponse

router = APIRouter(tags=["Staff — Shifts & Roster"])
BASE = "/tenant/{tenant_id}/staff"


def _uid() -> str:
    return str(uuid.uuid4())


@router.get(BASE + "/{staff_id}/shifts", response_model=List[StaffShiftResponse])
async def list_shifts(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "schedules:view")
    rows = (await db.scalars(select(StaffShift).where(
        StaffShift.staff_id == staff_id,
        StaffShift.is_deleted == False))).all()  # noqa: E712
    return [StaffShiftResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/shifts", response_model=StaffShiftResponse,
             status_code=status.HTTP_201_CREATED)
async def create_shift(
    tenant_id: int,
    staff_id: str,
    payload: StaffShiftCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "schedules:create")
    if payload.end_hour <= payload.start_hour:
        raise HTTPException(status_code=422, detail="End hour must be after start hour.")
    if payload.is_recurring and not payload.recurring_from:
        raise HTTPException(status_code=422, detail="Recurring shifts require a recurring_from date.")

    record = StaffShift(
        shift_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(
        db, current_user.get("user_id"), "CREATE", "staff_shift", record.shift_id,
        new_values={"staff_id": staff_id, "day_of_week": payload.day_of_week, "shift_type": payload.shift_type},
        request=request,
    )
    await db.commit()
    await db.refresh(record)
    return StaffShiftResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/shifts/{shift_id}", response_model=StaffShiftResponse)
async def update_shift(
    tenant_id: int,
    staff_id: str,
    shift_id: str,
    payload: StaffShiftUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "schedules:edit")
    record = await db.scalar(select(StaffShift).where(
        StaffShift.shift_id == shift_id,
        StaffShift.staff_id == staff_id,
        StaffShift.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Shift not found")

    updates = payload.model_dump(exclude_unset=True)
    new_start = updates.get("start_hour", record.start_hour)
    new_end = updates.get("end_hour", record.end_hour)
    if new_end <= new_start:
        raise HTTPException(status_code=422, detail="End hour must be after start hour.")
    if updates.get("is_recurring", record.is_recurring) and not updates.get("recurring_from", record.recurring_from):
        raise HTTPException(status_code=422, detail="Recurring shifts require a recurring_from date.")

    for f, v in updates.items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(
        db, current_user.get("user_id"), "UPDATE", "staff_shift", shift_id,
        new_values={**updates, "staff_id": staff_id},
        request=request,
    )
    await db.commit()
    await db.refresh(record)
    return StaffShiftResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    tenant_id: int,
    staff_id: str,
    shift_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "schedules:delete")
    record = await db.scalar(select(StaffShift).where(
        StaffShift.shift_id == shift_id,
        StaffShift.staff_id == staff_id,
        StaffShift.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Shift not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(
        db, current_user.get("user_id"), "DELETE", "staff_shift", shift_id,
        old_values={"staff_id": staff_id, "shift_type": record.shift_type},
        request=request,
    )
    await db.commit()
