"""Staff Timesheets router — timesheet headers and lines."""
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models.staff_timesheet_header import StaffTimesheetHeader
from app.models.staff_timesheet_line import StaffTimesheetLine
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_timesheets import (
    StaffTimesheetHeaderCreate, StaffTimesheetHeaderUpdate, StaffTimesheetHeaderResponse,
    StaffTimesheetLineCreate, StaffTimesheetLineResponse,
)

router = APIRouter(tags=["Staff — Timesheets"])

BASE = "/tenant/{tenant_id}/staff"


def _uid() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
# TIMESHEETS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/timesheets", response_model=List[StaffTimesheetHeaderResponse])
async def list_timesheets(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffTimesheetHeader).where(
        StaffTimesheetHeader.staff_id == staff_id,
        StaffTimesheetHeader.is_deleted == False).order_by(StaffTimesheetHeader.work_date.desc()))).all()  # noqa: E712
    return [StaffTimesheetHeaderResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/timesheets", response_model=StaffTimesheetHeaderResponse,
             status_code=status.HTTP_201_CREATED)
async def create_timesheet(
    tenant_id: int,
    staff_id: str,
    payload: StaffTimesheetHeaderCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:timesheets")
    record = StaffTimesheetHeader(
        timesheet_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_timesheet_header", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffTimesheetHeaderResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/timesheets/{timesheet_id}", response_model=StaffTimesheetHeaderResponse)
async def update_timesheet(
    tenant_id: int,
    staff_id: str,
    timesheet_id: str,
    payload: StaffTimesheetHeaderUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:timesheets")
    record = await db.scalar(select(StaffTimesheetHeader).where(
        StaffTimesheetHeader.timesheet_id == timesheet_id,
        StaffTimesheetHeader.staff_id == staff_id,
        StaffTimesheetHeader.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_timesheet_header", timesheet_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffTimesheetHeaderResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/timesheets/{timesheet_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_timesheet(
    tenant_id: int,
    staff_id: str,
    timesheet_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:timesheets")
    record = await db.scalar(select(StaffTimesheetHeader).where(
        StaffTimesheetHeader.timesheet_id == timesheet_id,
        StaffTimesheetHeader.staff_id == staff_id,
        StaffTimesheetHeader.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_timesheet_header", timesheet_id, request=request)
    await db.commit()


@router.get(BASE + "/{staff_id}/timesheets/{timesheet_id}/lines", response_model=List[StaffTimesheetLineResponse])
async def list_timesheet_lines(
    tenant_id: int,
    staff_id: str,
    timesheet_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffTimesheetLine).where(
        StaffTimesheetLine.timesheet_id == timesheet_id,
        StaffTimesheetLine.is_deleted == False))).all()  # noqa: E712
    return [StaffTimesheetLineResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/timesheets/{timesheet_id}/lines",
             response_model=StaffTimesheetLineResponse, status_code=status.HTTP_201_CREATED)
async def add_timesheet_line(
    tenant_id: int,
    staff_id: str,
    timesheet_id: str,
    payload: StaffTimesheetLineCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:timesheets")
    record = StaffTimesheetLine(
        timesheet_line_id=_uid(), tenant_id=tenant_id, timesheet_id=timesheet_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_timesheet_line", timesheet_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffTimesheetLineResponse.model_validate(record)
