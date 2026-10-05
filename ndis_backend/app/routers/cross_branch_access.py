"""Cross-Branch Access router — 4.1–4.7."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db, get_tenant_session
from app.models import AppUser, Branch, CrossBranchAccess
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas.cross_branch_access import (
    ApproveRequest,
    CrossBranchAccessRequest,
    CrossBranchAccessResponse,
    EmergencyAccessRequest,
    RejectRequest,
    ReviewRequest,
    RevokeRequest,
)

router = APIRouter(tags=["Cross-Branch Access"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auto_expire(rec: CrossBranchAccess) -> CrossBranchAccess:
    """If an active record is past its access_end, mark it expired in-memory."""
    if rec.status == "active" and rec.access_end:
        if rec.access_end < datetime.now(timezone.utc):
            rec.status = "expired"
            rec.is_active = False
    return rec


async def _resolve_user_name(common_db: AsyncSession, user_id: str) -> str:
    u = await common_db.scalar(select(AppUser).where(AppUser.user_id == user_id))
    if u:
        return f"{u.first_name} {u.last_name}"
    return user_id


# ── 4.2  List + Create requests ───────────────────────────────────────────────

@router.get("/tenant/{tenant_id}/cross-branch-access", response_model=List[CrossBranchAccessResponse])
async def list_cross_branch_access(
    tenant_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    branch_id: Optional[int] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[CrossBranchAccessResponse]:
    """4.1 — List all cross-branch access records (with optional filters)."""
    verify_tenant_access(tenant_id, current_user)

    q = select(CrossBranchAccess).where(CrossBranchAccess.is_deleted == False)  # noqa: E712
    if status_filter:
        q = q.where(CrossBranchAccess.status == status_filter)
    if branch_id:
        q = q.where(
            (CrossBranchAccess.target_branch_id == branch_id) |
            (CrossBranchAccess.home_branch_id == branch_id)
        )
    q = q.order_by(CrossBranchAccess.requested_at.desc())

    rows = (await db.scalars(q)).all()
    # Auto-expire in-memory
    result = []
    for r in rows:
        r = _auto_expire(r)
        result.append(CrossBranchAccessResponse.model_validate(r))
    return result


@router.post(
    "/tenant/{tenant_id}/cross-branch-access",
    response_model=CrossBranchAccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_access_request(
    tenant_id: int,
    payload: CrossBranchAccessRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> CrossBranchAccessResponse:
    """4.2 — Submit a planned cross-branch access request."""
    verify_tenant_access(tenant_id, current_user)

    # Validate target branch exists
    target = await db.scalar(select(Branch).where(
        Branch.branch_id == payload.target_branch_id,
        Branch.is_deleted == False,  # noqa: E712
    ))
    if not target:
        raise HTTPException(status_code=404, detail="Target branch not found")

    rec = CrossBranchAccess(
        staff_user_id=payload.staff_user_id,
        home_branch_id=payload.home_branch_id,
        target_branch_id=payload.target_branch_id,
        access_reason=payload.access_reason,
        services_description=payload.services_description,
        access_start=payload.access_start,
        access_end=payload.access_end,
        participant_id=payload.participant_id,
        participant_name=payload.participant_name,
        permitted_activities=payload.permitted_activities,
        access_type="planned",
        is_emergency=False,
        requires_review=False,
        status="pending",
        requested_by=current_user["user_id"],
        is_active=True,
        is_deleted=False,
    )
    db.add(rec)
    await db.flush()

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="CREATE", table_name="cross_branch_access",
        record_id=str(rec.access_id),
        new_values=payload.model_dump(mode="json"),
        request=request,
    )
    await db.commit()
    await db.refresh(rec)
    return CrossBranchAccessResponse.model_validate(rec)


# ── 4.5  Emergency access ─────────────────────────────────────────────────────

@router.post(
    "/tenant/{tenant_id}/cross-branch-access/emergency",
    response_model=CrossBranchAccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_emergency_access(
    tenant_id: int,
    payload: EmergencyAccessRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> CrossBranchAccessResponse:
    """4.5 — Immediate emergency access; bypasses approval and flags for admin review."""
    verify_tenant_access(tenant_id, current_user)

    target = await db.scalar(select(Branch).where(
        Branch.branch_id == payload.target_branch_id,
        Branch.is_deleted == False,  # noqa: E712
    ))
    if not target:
        raise HTTPException(status_code=404, detail="Target branch not found")

    now = datetime.now(timezone.utc)
    rec = CrossBranchAccess(
        staff_user_id=payload.staff_user_id,
        home_branch_id=payload.home_branch_id,
        target_branch_id=payload.target_branch_id,
        access_reason=payload.emergency_reason,
        emergency_reason=payload.emergency_reason,
        services_description=payload.services_description,
        access_start=payload.access_start or now,
        access_end=payload.access_end,
        participant_id=payload.participant_id,
        participant_name=payload.participant_name,
        permitted_activities=payload.permitted_activities,
        access_type="emergency",
        is_emergency=True,
        requires_review=True,  # must be reviewed by admin
        status="active",       # immediately active
        approved_by=current_user["user_id"],
        approved_at=now,
        approval_comments="Emergency access — granted immediately, pending admin review.",
        requested_by=current_user["user_id"],
        is_active=True,
        is_deleted=False,
    )
    db.add(rec)
    await db.flush()

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="CREATE", table_name="cross_branch_access",
        record_id=str(rec.access_id),
        new_values={**payload.model_dump(mode="json"), "access_type": "emergency"},
        request=request,
    )
    await db.commit()
    await db.refresh(rec)
    return CrossBranchAccessResponse.model_validate(rec)


# ── Single record ─────────────────────────────────────────────────────────────

@router.get("/tenant/{tenant_id}/cross-branch-access/{access_id}", response_model=CrossBranchAccessResponse)
async def get_cross_branch_access(
    tenant_id: int,
    access_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> CrossBranchAccessResponse:
    verify_tenant_access(tenant_id, current_user)
    rec = await _get_or_404(db, access_id)
    return CrossBranchAccessResponse.model_validate(_auto_expire(rec))


# ── 4.3  Approve ─────────────────────────────────────────────────────────────

@router.patch("/tenant/{tenant_id}/cross-branch-access/{access_id}/approve", response_model=CrossBranchAccessResponse)
async def approve_access(
    tenant_id: int,
    access_id: int,
    payload: ApproveRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> CrossBranchAccessResponse:
    """4.3 — Admin approves a pending access request."""
    verify_tenant_access(tenant_id, current_user)
    rec = await _get_or_404(db, access_id)

    if rec.status != "pending":
        raise HTTPException(status_code=409, detail=f"Cannot approve — current status is '{rec.status}'")

    now = datetime.now(timezone.utc)
    rec.status = "approved"
    rec.approved_by = current_user["user_id"]
    rec.approved_at = now
    rec.approval_comments = payload.approval_comments
    if payload.access_start:
        rec.access_start = payload.access_start
    if payload.access_end:
        rec.access_end = payload.access_end
    if payload.permitted_activities:
        rec.permitted_activities = payload.permitted_activities

    # If access_start is now or in the past, activate immediately
    start = rec.access_start or now
    if start <= now:
        rec.status = "active"

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="UPDATE", table_name="cross_branch_access",
        record_id=str(access_id),
        new_values={"status": rec.status, "approved_by": rec.approved_by, "approval_comments": rec.approval_comments},
        request=request,
    )
    await db.commit()
    await db.refresh(rec)
    return CrossBranchAccessResponse.model_validate(rec)


# ── 4.3  Reject ──────────────────────────────────────────────────────────────

@router.patch("/tenant/{tenant_id}/cross-branch-access/{access_id}/reject", response_model=CrossBranchAccessResponse)
async def reject_access(
    tenant_id: int,
    access_id: int,
    payload: RejectRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> CrossBranchAccessResponse:
    """4.3 — Admin rejects a pending access request."""
    verify_tenant_access(tenant_id, current_user)
    rec = await _get_or_404(db, access_id)

    if rec.status != "pending":
        raise HTTPException(status_code=409, detail=f"Cannot reject — current status is '{rec.status}'")

    now = datetime.now(timezone.utc)
    rec.status = "rejected"
    rec.rejected_by = current_user["user_id"]
    rec.rejected_at = now
    rec.rejection_reason = payload.rejection_reason
    rec.is_active = False

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="UPDATE", table_name="cross_branch_access",
        record_id=str(access_id),
        new_values={"status": "rejected", "rejection_reason": rec.rejection_reason},
        request=request,
    )
    await db.commit()
    await db.refresh(rec)
    return CrossBranchAccessResponse.model_validate(rec)


# ── Revoke ────────────────────────────────────────────────────────────────────

@router.patch("/tenant/{tenant_id}/cross-branch-access/{access_id}/revoke", response_model=CrossBranchAccessResponse)
async def revoke_access(
    tenant_id: int,
    access_id: int,
    payload: RevokeRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> CrossBranchAccessResponse:
    """Revoke an active or approved access grant."""
    verify_tenant_access(tenant_id, current_user)
    rec = await _get_or_404(db, access_id)

    if rec.status not in ("active", "approved"):
        raise HTTPException(status_code=409, detail=f"Cannot revoke — current status is '{rec.status}'")

    now = datetime.now(timezone.utc)
    rec.status = "revoked"
    rec.revoked_by = current_user["user_id"]
    rec.revoked_at = now
    rec.revoke_reason = payload.revoke_reason
    rec.is_active = False

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="UPDATE", table_name="cross_branch_access",
        record_id=str(access_id),
        new_values={"status": "revoked", "revoke_reason": rec.revoke_reason},
        request=request,
    )
    await db.commit()
    await db.refresh(rec)
    return CrossBranchAccessResponse.model_validate(rec)


# ── Emergency review ──────────────────────────────────────────────────────────

@router.patch("/tenant/{tenant_id}/cross-branch-access/{access_id}/review", response_model=CrossBranchAccessResponse)
async def review_emergency_access(
    tenant_id: int,
    access_id: int,
    payload: ReviewRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> CrossBranchAccessResponse:
    """4.5 — Admin reviews an emergency access record."""
    verify_tenant_access(tenant_id, current_user)
    rec = await _get_or_404(db, access_id)

    if not rec.is_emergency:
        raise HTTPException(status_code=400, detail="Record is not an emergency access")

    now = datetime.now(timezone.utc)
    rec.requires_review = False
    rec.reviewed_by = current_user["user_id"]
    rec.reviewed_at = now
    rec.review_notes = payload.review_notes

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="UPDATE", table_name="cross_branch_access",
        record_id=str(access_id),
        new_values={"requires_review": False, "review_notes": rec.review_notes},
        request=request,
    )
    await db.commit()
    await db.refresh(rec)
    return CrossBranchAccessResponse.model_validate(rec)


# ── 4.7  Audit trail ─────────────────────────────────────────────────────────

@router.get("/tenant/{tenant_id}/cross-branch-access-audit")
async def cross_branch_audit_trail(
    tenant_id: int,
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[dict]:
    """4.7 — Full audit trail: all CBA records ordered by latest activity."""
    verify_tenant_access(tenant_id, current_user)

    rows = (await db.scalars(
        select(CrossBranchAccess)
        .where(CrossBranchAccess.is_deleted == False)  # noqa: E712
        .order_by(CrossBranchAccess.requested_at.desc())
        .limit(limit)
    )).all()

    result = []
    for r in rows:
        r = _auto_expire(r)
        result.append({
            "access_id":        r.access_id,
            "staff_user_id":    r.staff_user_id,
            "home_branch_id":   r.home_branch_id,
            "target_branch_id": r.target_branch_id,
            "participant_name": r.participant_name,
            "access_type":      r.access_type,
            "status":           r.status,
            "is_emergency":     r.is_emergency,
            "requires_review":  r.requires_review,
            "access_reason":    r.access_reason,
            "access_start":     r.access_start.isoformat() if r.access_start else None,
            "access_end":       r.access_end.isoformat()   if r.access_end   else None,
            "requested_by":     r.requested_by,
            "requested_at":     r.requested_at.isoformat(),
            "approved_by":      r.approved_by,
            "approved_at":      r.approved_at.isoformat()  if r.approved_at  else None,
            "rejected_by":      r.rejected_by,
            "rejected_at":      r.rejected_at.isoformat()  if r.rejected_at  else None,
            "revoked_by":       r.revoked_by,
            "revoked_at":       r.revoked_at.isoformat()   if r.revoked_at   else None,
            "reviewed_by":      r.reviewed_by,
            "reviewed_at":      r.reviewed_at.isoformat()  if r.reviewed_at  else None,
        })
    return result


# ── Private helper ────────────────────────────────────────────────────────────

async def _get_or_404(db: AsyncSession, access_id: int) -> CrossBranchAccess:
    rec = await db.scalar(select(CrossBranchAccess).where(
        CrossBranchAccess.access_id == access_id,
        CrossBranchAccess.is_deleted == False,  # noqa: E712
    ))
    if not rec:
        raise HTTPException(status_code=404, detail="Cross-branch access record not found")
    return rec
