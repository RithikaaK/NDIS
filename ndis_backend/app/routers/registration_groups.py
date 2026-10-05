"""Tenant Registration Groups router — tenant schema scoped."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models import TenantRegistrationGroup
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import MessageResponse
from app.schemas.tenant_registration_group import (
    TenantRegistrationGroupCreate,
    TenantRegistrationGroupResponse,
)

router = APIRouter(tags=["Registration Groups"])

TTL_REG_GROUPS = 600


@router.get(
    "/tenant/{tenant_id}/registration-groups",
    response_model=List[TenantRegistrationGroupResponse],
)
async def list_registration_groups(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[TenantRegistrationGroupResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:reg_groups"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    groups = (await db.scalars(
        select(TenantRegistrationGroup)
        .where(
            TenantRegistrationGroup.tenant_id == tenant_id,
            TenantRegistrationGroup.is_active == True,  # noqa: E712
        )
        .order_by(TenantRegistrationGroup.registration_group_code)
    )).all()
    result = [TenantRegistrationGroupResponse.model_validate(g).model_dump(mode="json") for g in groups]
    await cache_set(key, result, ttl=TTL_REG_GROUPS)
    return result


@router.post(
    "/tenant/{tenant_id}/registration-groups",
    response_model=TenantRegistrationGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_registration_group(
    tenant_id: int,
    payload: TenantRegistrationGroupCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantRegistrationGroupResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(TenantRegistrationGroup).where(
        TenantRegistrationGroup.tenant_id == tenant_id,
        TenantRegistrationGroup.registration_group_code == payload.registration_group_code.strip().upper(),
    ))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Registration group '{payload.registration_group_code}' already exists",
        )

    rg = TenantRegistrationGroup(
        tenant_id=tenant_id,
        registration_group_code=payload.registration_group_code.strip().upper(),
        registration_group_name=payload.registration_group_name.strip(),
        is_active=payload.is_active,
    )
    db.add(rg)
    await db.flush()

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="CREATE", table_name="tenant_registration_group",
        record_id=str(rg.tenant_reg_group_id),
        new_values=payload.model_dump(), request=request,
    )
    await db.commit()
    await db.refresh(rg)
    await cache_delete(f"tenant:{tenant_id}:reg_groups")
    return TenantRegistrationGroupResponse.model_validate(rg)


@router.delete(
    "/tenant/{tenant_id}/registration-groups/{group_id}",
    response_model=MessageResponse,
)
async def delete_registration_group(
    tenant_id: int,
    group_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    rg = await db.scalar(select(TenantRegistrationGroup).where(
        TenantRegistrationGroup.tenant_reg_group_id == group_id,
        TenantRegistrationGroup.tenant_id == tenant_id,
    ))
    if not rg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration group not found")

    rg_code = rg.registration_group_code
    rg_name = rg.registration_group_name
    await db.delete(rg)
    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="DELETE", table_name="tenant_registration_group",
        record_id=str(group_id),
        old_values={"registration_group_code": rg_code, "registration_group_name": rg_name},
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:reg_groups")
    return MessageResponse(message=f"Registration group '{rg_name}' removed")
