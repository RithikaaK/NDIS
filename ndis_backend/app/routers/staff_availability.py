"""Staff Availability router."""
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models.staff_availability import StaffAvailability
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_availability import (
    StaffAvailabilityCreate, StaffAvailabilityUpdate, StaffAvailabilityResponse,
)

router = APIRouter(tags=["Staff — Availability"])

BASE = "/tenant/{tenant_id}/staff"


def _uid() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
# AVAILABILITY
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/availability", response_model=List[StaffAvailabilityResponse])
async def list_availability(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffAvailability).where(
        StaffAvailability.staff_id == staff_id,
        StaffAvailability.is_deleted == False))).all()  # noqa: E712
    return [StaffAvailabilityResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/availability", response_model=StaffAvailabilityResponse,
             status_code=status.HTTP_201_CREATED)
async def create_availability(
    tenant_id: int,
    staff_id: str,
    payload: StaffAvailabilityCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = StaffAvailability(
        availability_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_availability", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffAvailabilityResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/availability/{availability_id}",
              response_model=StaffAvailabilityResponse)
async def update_availability(
    tenant_id: int,
    staff_id: str,
    availability_id: str,
    payload: StaffAvailabilityUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffAvailability).where(
        StaffAvailability.availability_id == availability_id,
        StaffAvailability.staff_id == staff_id,
        StaffAvailability.is_deleted == False))  # noqa: E712
    from fastapi import HTTPException
    if not record:
        raise HTTPException(status_code=404, detail="Availability record not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_availability", availability_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffAvailabilityResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/availability/{availability_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability(
    tenant_id: int,
    staff_id: str,
    availability_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffAvailability).where(
        StaffAvailability.availability_id == availability_id,
        StaffAvailability.staff_id == staff_id,
        StaffAvailability.is_deleted == False))  # noqa: E712
    from fastapi import HTTPException
    if not record:
        raise HTTPException(status_code=404, detail="Availability record not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_availability", availability_id, request=request)
    await db.commit()
