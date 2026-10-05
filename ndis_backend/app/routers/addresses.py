"""Tenant Addresses router — tenant schema scoped."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models import TenantAddress
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import MessageResponse, TenantAddressCreate, TenantAddressResponse, TenantAddressUpdate

router = APIRouter(tags=["Tenant Addresses"])

TTL_ADDRESSES = 300


@router.get("/tenant/{tenant_id}/addresses", response_model=List[TenantAddressResponse])
async def list_tenant_addresses(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[TenantAddressResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:addresses"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    addresses = (await db.scalars(
        select(TenantAddress)
        .where(TenantAddress.tenant_id == tenant_id)
        .order_by(TenantAddress.address_id)
    )).all()
    result = [TenantAddressResponse.model_validate(a).model_dump(mode="json") for a in addresses]
    await cache_set(key, result, ttl=TTL_ADDRESSES)
    return result


@router.post("/tenant/{tenant_id}/addresses", response_model=TenantAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_address(
    tenant_id: int,
    payload: TenantAddressCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantAddressResponse:
    verify_tenant_access(tenant_id, current_user)

    if payload.is_primary:
        primaries = (await db.scalars(select(TenantAddress).where(
            TenantAddress.tenant_id == tenant_id,
            TenantAddress.is_primary == True,  # noqa: E712
        ))).all()
        for addr in primaries:
            addr.is_primary = False

    new_address = TenantAddress(
        tenant_id=tenant_id,
        address_type=payload.address_type,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        suburb=payload.suburb,
        state_code=payload.state_code,
        postcode=payload.postcode,
        country_code=payload.country_code,
        is_primary=payload.is_primary,
    )
    db.add(new_address)
    await db.flush()

    await log_audit(db=db, user_id=current_user["user_id"],
                    action="CREATE", table_name="tenant_address",
                    record_id=str(new_address.address_id), new_values=payload.model_dump(), request=request)
    await db.commit()
    await db.refresh(new_address)
    await cache_delete(f"tenant:{tenant_id}:addresses")
    return TenantAddressResponse.model_validate(new_address)


@router.put("/tenant/{tenant_id}/addresses/{address_id}", response_model=TenantAddressResponse)
async def update_tenant_address(
    tenant_id: int,
    address_id: int,
    payload: TenantAddressUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantAddressResponse:
    verify_tenant_access(tenant_id, current_user)

    address = await db.scalar(select(TenantAddress).where(
        TenantAddress.address_id == address_id,
        TenantAddress.tenant_id == tenant_id,
    ))
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

    if payload.is_primary:
        primaries = (await db.scalars(select(TenantAddress).where(
            TenantAddress.tenant_id == tenant_id,
            TenantAddress.is_primary == True,  # noqa: E712
            TenantAddress.address_id != address_id,
        ))).all()
        for addr in primaries:
            addr.is_primary = False

    old_values = {c.name: getattr(address, c.name) for c in address.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(address, field, val)

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="UPDATE", table_name="tenant_address",
        record_id=str(address_id),
        old_values=old_values, new_values=update_data, request=request,
    )
    await db.commit()
    await db.refresh(address)
    await cache_delete(f"tenant:{tenant_id}:addresses")
    return TenantAddressResponse.model_validate(address)


@router.delete("/tenant/{tenant_id}/addresses/{address_id}", response_model=MessageResponse)
async def delete_tenant_address(
    tenant_id: int,
    address_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    address = await db.scalar(select(TenantAddress).where(
        TenantAddress.address_id == address_id,
        TenantAddress.tenant_id == tenant_id,
    ))
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

    addr_type = address.address_type
    await db.delete(address)
    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="DELETE", table_name="tenant_address",
        record_id=str(address_id),
        old_values={"address_type": addr_type, "address_id": address_id},
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:addresses")
    return MessageResponse(message=f"Address '{addr_type}' (id={address_id}) deleted")
