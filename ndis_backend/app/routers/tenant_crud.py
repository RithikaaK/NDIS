"""Tenant CRUD router — list, get, update, soft-delete."""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_db, get_tenant_session
from app.models import Tenant
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import MessageResponse, TenantListResponse, TenantResponse, TenantUpdate

router = APIRouter(tags=["Tenant"])

TTL_TENANT = 300


@router.get("/tenant", response_model=TenantListResponse)
async def list_tenants(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantListResponse:
    stmt = select(Tenant).where(
        Tenant.tenant_id == current_user["tenant_id"],
        Tenant.is_deleted == False,  # noqa: E712
    )
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(or_(
            Tenant.organisation_name.ilike(term),
            Tenant.tenant_code.ilike(term),
            Tenant.abn.ilike(term),
        ))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = (await db.scalars(stmt.offset(skip).limit(limit))).all()
    return TenantListResponse(
        total=total, skip=skip, limit=limit,
        items=[TenantResponse.model_validate(i) for i in items],
    )


@router.get("/tenant/{tenant_id}", response_model=TenantResponse)
async def get_tenant_by_id(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    tenant = await db.scalar(
        select(Tenant).where(Tenant.tenant_id == tenant_id, Tenant.is_deleted == False)  # noqa: E712
    )
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    result = TenantResponse.model_validate(tenant).model_dump(mode="json")
    await cache_set(key, result, ttl=TTL_TENANT)
    return result


@router.put("/tenant/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> TenantResponse:
    verify_tenant_access(tenant_id, current_user)
    tenant = await db.scalar(
        select(Tenant).where(Tenant.tenant_id == tenant_id, Tenant.is_deleted == False)  # noqa: E712
    )
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    old_data = {c.name: getattr(tenant, c.name) for c in tenant.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await log_audit(db=tenant_db, user_id=current_user["user_id"],
                    action="UPDATE", table_name="tenant", record_id=str(tenant_id),
                    old_values=old_data, new_values=update_data, request=request)
    await db.commit()
    await tenant_db.commit()
    await db.refresh(tenant)
    await cache_delete(f"tenant:{tenant_id}")
    return TenantResponse.model_validate(tenant)


@router.delete("/tenant/{tenant_id}", response_model=MessageResponse)
async def delete_tenant(
    tenant_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)
    tenant = await db.scalar(
        select(Tenant).where(Tenant.tenant_id == tenant_id, Tenant.is_deleted == False)  # noqa: E712
    )
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    tenant.is_deleted = True
    tenant.deleted_at = datetime.now(timezone.utc)
    tenant.status = "Inactive"

    await log_audit(db=tenant_db, user_id=current_user["user_id"],
                    action="SOFT_DELETE", table_name="tenant", record_id=str(tenant_id),
                    request=request)
    await db.commit()
    await tenant_db.commit()
    await cache_delete(f"tenant:{tenant_id}")
    return MessageResponse(message=f"Tenant {tenant.organisation_name} has been soft-deleted")
