"""Branches router — tenant-schema scoped."""
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_db, get_tenant_session
from app.models import AppUser, Branch
from app.models.program import Program
from app.models.program_branch import ProgramBranch
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import BranchCreate, BranchResponse, BranchUpdate, MessageResponse
from app.schemas.branch import BranchStaffResponse, BranchProgramResponse

router = APIRouter(tags=["Branches"])

TTL_BRANCHES = 300


@router.get("/tenant/{tenant_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[BranchResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:branches"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    branches = (await db.scalars(
        select(Branch)
        .where(Branch.is_deleted == False)  # noqa: E712
        .order_by(Branch.is_head_office.desc(), Branch.branch_id)
    )).all()
    result = [BranchResponse.model_validate(b).model_dump(mode="json") for b in branches]
    await cache_set(key, result, ttl=TTL_BRANCHES)
    return result


@router.post("/tenant/{tenant_id}/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    tenant_id: int,
    payload: BranchCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> BranchResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(Branch).where(
        Branch.branch_code == payload.branch_code.strip(),
        Branch.is_deleted == False,  # noqa: E712
    ))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Branch with code '{payload.branch_code}' already exists",
        )

    # Build branch — new optional fields (added by migration) are only set when
    # they have a value, so the INSERT doesn't fail on schemas not yet migrated.
    branch_kwargs: dict = dict(
        branch_code=payload.branch_code.strip().upper(),
        branch_name=payload.branch_name.strip(),
        phone=payload.phone,
        email=payload.email.lower() if payload.email else None,
        address_line1=payload.address_line1,
        suburb=payload.suburb,
        state_code=payload.state_code,
        postcode=payload.postcode,
        is_head_office=payload.is_head_office,
        is_active=payload.is_active,
        is_deleted=False,
    )
    # New extended fields — only add if not None (migration may not have run yet)
    for attr in ("branch_type", "parent_branch_id", "address_line2", "country",
                 "timezone", "operating_hours", "facilities", "notes"):
        val = getattr(payload, attr, None)
        if val is not None:
            branch_kwargs[attr] = val
    if payload.branch_status:
        branch_kwargs["branch_status"] = payload.branch_status
    branch = Branch(**branch_kwargs)
    db.add(branch)
    await db.flush()

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="CREATE",
        table_name="branch",
        record_id=str(branch.branch_id),
        new_values=payload.model_dump(),
        request=request,
    )
    await db.commit()
    await db.refresh(branch)
    await cache_delete(f"tenant:{tenant_id}:branches")
    return BranchResponse.model_validate(branch)


@router.get("/tenant/{tenant_id}/branches/{branch_id}", response_model=BranchResponse)
async def get_branch_by_id(
    tenant_id: int,
    branch_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> BranchResponse:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:branch:{branch_id}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    branch = await db.scalar(select(Branch).where(
        Branch.branch_id == branch_id,
        Branch.is_deleted == False,  # noqa: E712
    ))
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    result = BranchResponse.model_validate(branch).model_dump(mode="json")
    await cache_set(key, result, ttl=TTL_BRANCHES)
    return result


@router.put("/tenant/{tenant_id}/branches/{branch_id}", response_model=BranchResponse)
async def update_branch(
    tenant_id: int,
    branch_id: int,
    payload: BranchUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> BranchResponse:
    verify_tenant_access(tenant_id, current_user)

    branch = await db.scalar(select(Branch).where(
        Branch.branch_id == branch_id,
        Branch.is_deleted == False,  # noqa: E712
    ))
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    old_values = {c.name: getattr(branch, c.name) for c in branch.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(branch, field, val)

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="UPDATE",
        table_name="branch",
        record_id=str(branch_id),
        old_values=old_values,
        new_values=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(branch)
    await cache_delete(f"tenant:{tenant_id}:branches", f"tenant:{tenant_id}:branch:{branch_id}")
    return BranchResponse.model_validate(branch)


@router.delete("/tenant/{tenant_id}/branches/{branch_id}", response_model=MessageResponse)
async def delete_branch(
    tenant_id: int,
    branch_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    branch = await db.scalar(select(Branch).where(
        Branch.branch_id == branch_id,
        Branch.is_deleted == False,  # noqa: E712
    ))
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    if branch.is_head_office:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the Head Office branch",
        )

    branch.is_deleted = True
    branch.deleted_at = datetime.now(timezone.utc)
    branch.is_active = False

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="SOFT_DELETE",
        table_name="branch",
        record_id=str(branch_id),
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:branches", f"tenant:{tenant_id}:branch:{branch_id}")
    return MessageResponse(message=f"Branch {branch.branch_name} has been soft-deleted")


# ─── 3.6 Staff-to-Location Assignment ─────────────────────────────────────────

@router.get("/tenant/{tenant_id}/branches/{branch_id}/staff")
async def list_branch_staff(
    tenant_id: int,
    branch_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    common_db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Return all users whose primary branch is this branch_id (app_user lives in ndis_common)."""
    verify_tenant_access(tenant_id, current_user)

    users = (await common_db.scalars(
        select(AppUser).where(
            AppUser.tenant_id == tenant_id,
            AppUser.branch_id == branch_id,
            AppUser.is_deleted == False,  # noqa: E712
        )
    )).all()

    return [
        {
            "user_id": str(u.user_id),
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "mobile": u.mobile,
            "job_title": u.job_title,
            "is_active": u.is_active,
        }
        for u in users
    ]


# ─── 3.8 Program-to-Location Mapping ──────────────────────────────────────────

@router.get("/tenant/{tenant_id}/branches/{branch_id}/programs")
async def list_branch_programs(
    tenant_id: int,
    branch_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[dict]:
    """Return all programs mapped to this branch."""
    verify_tenant_access(tenant_id, current_user)

    rows = (await db.execute(
        select(ProgramBranch, Program)
        .join(Program, ProgramBranch.program_id == Program.program_id)
        .where(
            ProgramBranch.branch_id == branch_id,
            Program.is_deleted == False,  # noqa: E712
        )
    )).all()

    return [
        {
            "program_branch_id": pb.program_branch_id,
            "program_id": p.program_id,
            "program_name": p.program_name,
            "funding_type": p.funding_type,
            "is_active": pb.is_active,
        }
        for pb, p in rows
    ]


@router.post("/tenant/{tenant_id}/branches/{branch_id}/programs/{program_id}", status_code=status.HTTP_201_CREATED)
async def assign_program_to_branch(
    tenant_id: int,
    branch_id: int,
    program_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Link a program to this branch."""
    verify_tenant_access(tenant_id, current_user)

    # Check branch exists
    branch = await db.scalar(select(Branch).where(Branch.branch_id == branch_id, Branch.is_deleted == False))  # noqa: E712
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    # Check program exists
    program = await db.scalar(select(Program).where(Program.program_id == program_id, Program.is_deleted == False))  # noqa: E712
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # Check not already linked
    existing = await db.scalar(select(ProgramBranch).where(
        ProgramBranch.program_id == program_id,
        ProgramBranch.branch_id == branch_id,
    ))
    if existing:
        raise HTTPException(status_code=409, detail="Program already linked to this branch")

    pb = ProgramBranch(program_id=program_id, branch_id=branch_id, is_active=True)
    db.add(pb)
    await db.flush()
    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="CREATE", table_name="program_branch",
        record_id=str(pb.program_branch_id),
        new_values={"program_id": program_id, "branch_id": branch_id},
        request=request,
    )
    await db.commit()
    return {"program_branch_id": pb.program_branch_id, "program_id": program_id, "branch_id": branch_id}


@router.delete("/tenant/{tenant_id}/branches/{branch_id}/programs/{program_id}", response_model=MessageResponse)
async def remove_program_from_branch(
    tenant_id: int,
    branch_id: int,
    program_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    """Unlink a program from this branch."""
    verify_tenant_access(tenant_id, current_user)

    pb = await db.scalar(select(ProgramBranch).where(
        ProgramBranch.program_id == program_id,
        ProgramBranch.branch_id == branch_id,
    ))
    if not pb:
        raise HTTPException(status_code=404, detail="Program not linked to this branch")

    await db.delete(pb)
    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="DELETE", table_name="program_branch",
        record_id=str(pb.program_branch_id),
        request=request,
    )
    await db.commit()
    return MessageResponse(message="Program removed from branch")
