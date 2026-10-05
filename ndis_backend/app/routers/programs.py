"""Programs router — tenant-schema scoped."""
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models import Program, ProgramBranch
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import MessageResponse, ProgramCreate, ProgramResponse, ProgramUpdate

router = APIRouter(tags=["Programs"])

TTL_PROGRAMS = 300


@router.get("/tenant/{tenant_id}/programs", response_model=List[ProgramResponse])
async def list_programs(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[ProgramResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:programs"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    programs = (await db.scalars(
        select(Program)
        .where(Program.is_deleted == False)  # noqa: E712
        .options(selectinload(Program.program_branches))
        .order_by(Program.program_id)
    )).all()
    result = [ProgramResponse.model_validate(p).model_dump(mode="json") for p in programs]
    await cache_set(key, result, ttl=TTL_PROGRAMS)
    return result


@router.post("/tenant/{tenant_id}/programs", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    tenant_id: int,
    payload: ProgramCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> ProgramResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(Program).where(
        Program.program_code == payload.program_code.strip(),
        Program.is_deleted == False,  # noqa: E712
    ))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Program with code '{payload.program_code}' already exists",
        )

    program = Program(
        program_code=payload.program_code.strip().upper(),
        program_name=payload.program_name.strip(),
        description=payload.description,
        funding_type=payload.funding_type,
        is_active=payload.is_active,
        is_deleted=False,
    )
    db.add(program)
    await db.flush()

    if payload.branch_ids:
        for b_id in payload.branch_ids:
            db.add(ProgramBranch(program_id=program.program_id, branch_id=b_id))

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="CREATE",
        table_name="program",
        record_id=str(program.program_id),
        new_values=payload.model_dump(),
        request=request,
    )
    await db.commit()

    # Re-fetch with relationship loaded
    program = await db.scalar(
        select(Program)
        .where(Program.program_id == program.program_id)
        .options(selectinload(Program.program_branches))
    )
    await cache_delete(f"tenant:{tenant_id}:programs")
    return ProgramResponse.model_validate(program)


@router.put("/tenant/{tenant_id}/programs/{program_id}", response_model=ProgramResponse)
async def update_program(
    tenant_id: int,
    program_id: int,
    payload: ProgramUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> ProgramResponse:
    verify_tenant_access(tenant_id, current_user)

    program = await db.scalar(select(Program).where(
        Program.program_id == program_id,
        Program.is_deleted == False,  # noqa: E712
    ))
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    old_values = {c.name: getattr(program, c.name) for c in program.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(program, field, val)

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="UPDATE",
        table_name="program",
        record_id=str(program_id),
        old_values=old_values,
        new_values=update_data,
        request=request,
    )
    await db.commit()

    program = await db.scalar(
        select(Program)
        .where(Program.program_id == program_id)
        .options(selectinload(Program.program_branches))
    )
    await cache_delete(f"tenant:{tenant_id}:programs")
    return ProgramResponse.model_validate(program)


@router.delete("/tenant/{tenant_id}/programs/{program_id}", response_model=MessageResponse)
async def delete_program(
    tenant_id: int,
    program_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    program = await db.scalar(select(Program).where(
        Program.program_id == program_id,
        Program.is_deleted == False,  # noqa: E712
    ))
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    program.is_deleted = True
    program.deleted_at = datetime.now(timezone.utc)
    program.is_active = False

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="SOFT_DELETE",
        table_name="program",
        record_id=str(program_id),
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:programs")
    return MessageResponse(message=f"Program '{program.program_name}' has been deleted")


# ── Program → Branch assignments ───────────────────────────────────────────────

@router.post(
    "/tenant/{tenant_id}/programs/{program_id}/branches/{branch_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_branch_to_program(
    tenant_id: int,
    program_id: int,
    branch_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    """Assign a branch to a program (adds a program_branch row)."""
    verify_tenant_access(tenant_id, current_user)

    program = await db.scalar(select(Program).where(
        Program.program_id == program_id,
        Program.is_deleted == False,  # noqa: E712
    ))
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    existing = await db.scalar(select(ProgramBranch).where(
        ProgramBranch.program_id == program_id,
        ProgramBranch.branch_id == branch_id,
    ))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Branch {branch_id} is already assigned to program {program_id}",
        )

    db.add(ProgramBranch(program_id=program_id, branch_id=branch_id))
    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="ASSIGN",
        table_name="program_branch",
        record_id=f"{program_id}:{branch_id}",
        new_values={"program_id": program_id, "branch_id": branch_id},
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:programs")
    return MessageResponse(message=f"Branch {branch_id} assigned to program {program_id}")


@router.delete(
    "/tenant/{tenant_id}/programs/{program_id}/branches/{branch_id}",
    response_model=MessageResponse,
)
async def remove_branch_from_program(
    tenant_id: int,
    program_id: int,
    branch_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    """Remove a branch assignment from a program."""
    verify_tenant_access(tenant_id, current_user)

    pb = await db.scalar(select(ProgramBranch).where(
        ProgramBranch.program_id == program_id,
        ProgramBranch.branch_id == branch_id,
    ))
    if not pb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Branch {branch_id} is not assigned to program {program_id}",
        )

    await db.delete(pb)
    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="UNASSIGN",
        table_name="program_branch",
        record_id=f"{program_id}:{branch_id}",
        old_values={"program_id": program_id, "branch_id": branch_id},
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:programs")
    return MessageResponse(message=f"Branch {branch_id} removed from program {program_id}")
