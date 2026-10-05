"""Staff Employment router — employment info, probation, contracts, job roles, exit process."""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models.employment_information import EmploymentInformation
from app.models.staff_probation import StaffProbation
from app.models.staff_contract import StaffContract
from app.models.staff_roles import StaffRoles
from app.models.staff_exit_process import StaffExitProcess
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_employment import (
    EmploymentInformationCreate, EmploymentInformationResponse,
    StaffProbationCreate, StaffProbationResponse,
    StaffContractCreate, StaffContractResponse,
    StaffRolesCreate, StaffRolesResponse,
    StaffExitProcessCreate, StaffExitProcessResponse,
)

router = APIRouter(tags=["Staff — Employment"])

BASE = "/tenant/{tenant_id}/staff"


def _uid() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
# EMPLOYMENT INFORMATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/employment", response_model=Optional[EmploymentInformationResponse])
async def get_employment(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    record = await db.scalar(select(EmploymentInformation).where(
        EmploymentInformation.staff_id == staff_id, EmploymentInformation.is_deleted == False))  # noqa: E712
    return EmploymentInformationResponse.model_validate(record) if record else None


@router.put(BASE + "/{staff_id}/employment", response_model=EmploymentInformationResponse)
async def upsert_employment(
    tenant_id: int,
    staff_id: str,
    payload: EmploymentInformationCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")

    record = await db.scalar(select(EmploymentInformation).where(
        EmploymentInformation.staff_id == staff_id, EmploymentInformation.is_deleted == False))  # noqa: E712
    if record:
        for f, v in payload.model_dump(exclude_unset=True).items():
            setattr(record, f, v)
        record.updated_by = current_user.get("user_id")
    else:
        record = EmploymentInformation(
            employment_info_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
            **payload.model_dump(), created_by=current_user.get("user_id"),
        )
        db.add(record)
    await log_audit(db, current_user.get("user_id"), "UPSERT", "employment_information", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return EmploymentInformationResponse.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# PROBATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/probation", response_model=Optional[StaffProbationResponse])
async def get_probation(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    record = await db.scalar(select(StaffProbation).where(
        StaffProbation.staff_id == staff_id, StaffProbation.is_deleted == False))  # noqa: E712
    return StaffProbationResponse.model_validate(record) if record else None


@router.put(BASE + "/{staff_id}/probation", response_model=StaffProbationResponse)
async def upsert_probation(
    tenant_id: int,
    staff_id: str,
    payload: StaffProbationCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffProbation).where(
        StaffProbation.staff_id == staff_id, StaffProbation.is_deleted == False))  # noqa: E712
    if record:
        for f, v in payload.model_dump(exclude_unset=True).items():
            setattr(record, f, v)
        record.updated_by = current_user.get("user_id")
    else:
        record = StaffProbation(
            probation_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
            **payload.model_dump(), created_by=current_user.get("user_id"),
        )
        db.add(record)
    await log_audit(db, current_user.get("user_id"), "UPSERT", "staff_probation", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffProbationResponse.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTRACTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/contracts", response_model=List[StaffContractResponse])
async def list_contracts(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffContract).where(
        StaffContract.staff_id == staff_id, StaffContract.is_deleted == False))).all()  # noqa: E712
    return [StaffContractResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/contracts", response_model=StaffContractResponse,
             status_code=status.HTTP_201_CREATED)
async def create_contract(
    tenant_id: int,
    staff_id: str,
    payload: StaffContractCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = StaffContract(
        contract_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_contract", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffContractResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/contracts/{contract_id}", response_model=StaffContractResponse)
async def update_contract(
    tenant_id: int,
    staff_id: str,
    contract_id: str,
    payload: StaffContractCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffContract).where(
        StaffContract.contract_id == contract_id,
        StaffContract.staff_id == staff_id,
        StaffContract.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Contract not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_contract", contract_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffContractResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/contracts/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    tenant_id: int,
    staff_id: str,
    contract_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffContract).where(
        StaffContract.contract_id == contract_id,
        StaffContract.staff_id == staff_id,
        StaffContract.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Contract not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_contract", contract_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# STAFF ROLES (job roles)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/roles", response_model=List[StaffRolesResponse])
async def list_staff_roles(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffRoles).where(
        StaffRoles.staff_id == staff_id, StaffRoles.is_deleted == False))).all()  # noqa: E712
    return [StaffRolesResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/roles", response_model=StaffRolesResponse,
             status_code=status.HTTP_201_CREATED)
async def add_staff_role(
    tenant_id: int,
    staff_id: str,
    payload: StaffRolesCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = StaffRoles(
        staff_role_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_roles", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffRolesResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/roles/{role_id}", response_model=StaffRolesResponse)
async def update_staff_role(
    tenant_id: int,
    staff_id: str,
    role_id: str,
    payload: StaffRolesCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffRoles).where(
        StaffRoles.staff_role_id == role_id,
        StaffRoles.staff_id == staff_id,
        StaffRoles.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Role not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_roles", role_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffRolesResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff_role(
    tenant_id: int,
    staff_id: str,
    role_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffRoles).where(
        StaffRoles.staff_role_id == role_id,
        StaffRoles.staff_id == staff_id,
        StaffRoles.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Role not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_roles", role_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# EXIT PROCESS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/exit-process", response_model=Optional[StaffExitProcessResponse])
async def get_exit_process(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    record = await db.scalar(select(StaffExitProcess).where(
        StaffExitProcess.staff_id == staff_id, StaffExitProcess.is_deleted == False))  # noqa: E712
    return StaffExitProcessResponse.model_validate(record) if record else None


@router.put(BASE + "/{staff_id}/exit-process", response_model=StaffExitProcessResponse)
async def upsert_exit_process(
    tenant_id: int,
    staff_id: str,
    payload: StaffExitProcessCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffExitProcess).where(
        StaffExitProcess.staff_id == staff_id, StaffExitProcess.is_deleted == False))  # noqa: E712
    if record:
        for f, v in payload.model_dump(exclude_unset=True).items():
            setattr(record, f, v)
        record.updated_by = current_user.get("user_id")
    else:
        record = StaffExitProcess(
            exit_process_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
            **payload.model_dump(), created_by=current_user.get("user_id"),
        )
        db.add(record)
    await log_audit(db, current_user.get("user_id"), "UPSERT", "staff_exit_process", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffExitProcessResponse.model_validate(record)
