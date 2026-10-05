"""Staff Leave router — leave types master catalogue, leave requests, leave balances."""
import uuid
from decimal import Decimal
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db, get_tenant_session
from app.models.leave_type import LeaveType
from app.models.staff_leave_request import StaffLeaveRequest
from app.models.staff_leave_request_date import StaffLeaveRequestDate
from app.models.staff_leave_balance import StaffLeaveBalance
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_leave import (
    LeaveTypeCreate, LeaveTypeResponse,
    StaffLeaveRequestCreate, StaffLeaveRequestUpdate, StaffLeaveRequestResponse,
    StaffLeaveRequestDateCreate, StaffLeaveRequestDateResponse,
    StaffLeaveBalanceResponse,
)

router = APIRouter(tags=["Staff — Leave"])

BASE = "/tenant/{tenant_id}/staff"


def _short_id() -> str:
    return str(uuid.uuid4()).replace("-", "")[:20]


# ═══════════════════════════════════════════════════════════════════════════════
# LEAVE TYPES (master catalogue — uses common DB)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/leave-types", response_model=List[LeaveTypeResponse])
async def list_leave_types(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.scalars(
        select(LeaveType).where(LeaveType.is_active == True).order_by(LeaveType.leave_type_name)  # noqa: E712
    )).all()
    return [LeaveTypeResponse.model_validate(r) for r in rows]


@router.post("/leave-types", response_model=LeaveTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_type(
    payload: LeaveTypeCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = LeaveType(**payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return LeaveTypeResponse.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# LEAVE REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/leave-requests", response_model=List[StaffLeaveRequestResponse])
async def list_leave_requests(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffLeaveRequest).where(
        StaffLeaveRequest.staff_id == staff_id,
        StaffLeaveRequest.is_deleted == False).order_by(StaffLeaveRequest.created_at.desc()))).all()  # noqa: E712

    result = []
    for r in rows:
        resp = StaffLeaveRequestResponse.model_validate(r)
        date_rows = (await db.scalars(select(StaffLeaveRequestDate).where(
            StaffLeaveRequestDate.leave_request_id == r.leave_request_id,
            StaffLeaveRequestDate.is_deleted == False
        ).order_by(StaffLeaveRequestDate.leave_date.asc()))).all()

        valid_dates = [d.leave_date for d in date_rows if d.leave_date is not None]
        if valid_dates:
            resp.start_date = min(valid_dates)
            resp.end_date = max(valid_dates)
            resp.total_days = (resp.end_date - resp.start_date).days + 1
        resp.dates = [StaffLeaveRequestDateResponse.model_validate(d) for d in date_rows]
        result.append(resp)

    return result


@router.post(BASE + "/{staff_id}/leave-requests", response_model=StaffLeaveRequestResponse,
             status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    tenant_id: int,
    staff_id: str,
    payload: StaffLeaveRequestCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:leave")

    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be earlier than start date."
        )

    from datetime import date, timedelta
    dates_data = list(payload.dates or [])

    if payload.start_date and payload.end_date and not dates_data:
        curr = payload.start_date
        while curr <= payload.end_date:
            dates_data.append(StaffLeaveRequestDateCreate(
                leave_date=curr,
                leave_duration="Full Day",
                leave_hours=Decimal("7.6")
            ))
            curr += timedelta(days=1)

    leave_data = payload.model_dump(exclude={"dates", "start_date", "end_date", "total_days"})
    if not leave_data.get("submitted_date"):
        leave_data["submitted_date"] = date.today()

    leave_req = StaffLeaveRequest(
        leave_request_id=_short_id(), tenant_id=tenant_id, staff_id=staff_id,
        leave_status="Pending", **leave_data, created_by=current_user.get("user_id"),
    )
    db.add(leave_req)
    await db.flush()

    saved_dates = []
    for d in dates_data:
        d_dict = d.model_dump()
        if d_dict.get("leave_hours") is None:
            if d_dict.get("leave_duration") == "Full Day":
                d_dict["leave_hours"] = Decimal("7.6")
            elif d_dict.get("leave_duration") == "Half Day":
                d_dict["leave_hours"] = Decimal("3.8")
        rec = StaffLeaveRequestDate(
            leave_request_date_id=_short_id(), tenant_id=tenant_id,
            leave_request_id=leave_req.leave_request_id,
            **d_dict, created_by=current_user.get("user_id"),
        )
        db.add(rec)
        saved_dates.append(rec)

    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_leave_request", staff_id, request=request)
    await db.commit()
    await db.refresh(leave_req)

    resp = StaffLeaveRequestResponse.model_validate(leave_req)
    valid_dates = [d.leave_date for d in saved_dates if d.leave_date is not None]
    if valid_dates:
        resp.start_date = min(valid_dates)
        resp.end_date = max(valid_dates)
        resp.total_days = (resp.end_date - resp.start_date).days + 1
    elif payload.start_date and payload.end_date:
        resp.start_date = payload.start_date
        resp.end_date = payload.end_date
        resp.total_days = (payload.end_date - payload.start_date).days + 1
    resp.dates = [StaffLeaveRequestDateResponse.model_validate(d) for d in saved_dates]
    return resp


@router.patch(BASE + "/{staff_id}/leave-requests/{leave_request_id}",
              response_model=StaffLeaveRequestResponse)
async def update_leave_request(
    tenant_id: int,
    staff_id: str,
    leave_request_id: str,
    payload: StaffLeaveRequestUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:leave")
    record = await db.scalar(select(StaffLeaveRequest).where(
        StaffLeaveRequest.leave_request_id == leave_request_id,
        StaffLeaveRequest.staff_id == staff_id,
        StaffLeaveRequest.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Leave request not found")
    old = {"leave_status": record.leave_status}
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_leave_request", leave_request_id,
                    old_values=old, new_values=payload.model_dump(exclude_unset=True), request=request)
    await db.commit()
    await db.refresh(record)
    return StaffLeaveRequestResponse.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# LEAVE BALANCE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/leave-balances", response_model=List[StaffLeaveBalanceResponse])
async def list_leave_balances(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffLeaveBalance).where(
        StaffLeaveBalance.staff_id == staff_id,
        StaffLeaveBalance.is_deleted == False,
        StaffLeaveBalance.is_active == True))).all()  # noqa: E712
    return [StaffLeaveBalanceResponse.model_validate(r) for r in rows]
