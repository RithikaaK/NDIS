"""Tenant Service States router — tenant schema scoped."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models import TenantServiceState
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import MessageResponse
from app.schemas.tenant_service_state import TenantServiceStateCreate, TenantServiceStateResponse

router = APIRouter(tags=["Service States"])

TTL_SERVICE_STATES = 600


@router.get("/tenant/{tenant_id}/service-states", response_model=List[TenantServiceStateResponse])
async def list_service_states(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[TenantServiceStateResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:service_states"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    states = (await db.scalars(
        select(TenantServiceState)
        .where(TenantServiceState.tenant_id == tenant_id)
        .order_by(TenantServiceState.state_code)
    )).all()
    result = [TenantServiceStateResponse.model_validate(s).model_dump(mode="json") for s in states]
    await cache_set(key, result, ttl=TTL_SERVICE_STATES)
    return result


@router.post(
    "/tenant/{tenant_id}/service-states",
    response_model=TenantServiceStateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_state(
    tenant_id: int,
    payload: TenantServiceStateCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantServiceStateResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(TenantServiceState).where(
        TenantServiceState.tenant_id == tenant_id,
        TenantServiceState.state_code == payload.state_code.upper().strip(),
    ))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service state '{payload.state_code}' already exists for this tenant",
        )

    ss = TenantServiceState(
        tenant_id=tenant_id,
        state_code=payload.state_code.upper().strip(),
        is_active=payload.is_active,
    )
    db.add(ss)
    await db.flush()

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="CREATE", table_name="tenant_service_state",
        record_id=str(ss.service_state_id),
        new_values=payload.model_dump(), request=request,
    )
    await db.commit()
    await db.refresh(ss)
    await cache_delete(f"tenant:{tenant_id}:service_states")
    return TenantServiceStateResponse.model_validate(ss)


@router.delete("/tenant/{tenant_id}/service-states/{service_state_id}", response_model=MessageResponse)
async def delete_service_state(
    tenant_id: int,
    service_state_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    ss = await db.scalar(select(TenantServiceState).where(
        TenantServiceState.service_state_id == service_state_id,
        TenantServiceState.tenant_id == tenant_id,
    ))
    if not ss:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service state not found")

    state_code = ss.state_code
    await db.delete(ss)
    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="DELETE", table_name="tenant_service_state",
        record_id=str(service_state_id),
        old_values={"state_code": state_code}, request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:service_states")
    return MessageResponse(message=f"Service state '{state_code}' removed")
