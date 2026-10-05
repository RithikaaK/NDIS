"""Tenant Contacts router — tenant schema scoped."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models import TenantContact
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import MessageResponse, TenantContactCreate, TenantContactResponse, TenantContactUpdate

router = APIRouter(tags=["Tenant Contacts"])

TTL_CONTACTS = 300


@router.get("/tenant/{tenant_id}/contacts", response_model=List[TenantContactResponse])
async def list_tenant_contacts(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[TenantContactResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:contacts"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    contacts = (await db.scalars(
        select(TenantContact)
        .where(TenantContact.tenant_id == tenant_id)
        .order_by(TenantContact.contact_id)
    )).all()
    result = [TenantContactResponse.model_validate(c).model_dump(mode="json") for c in contacts]
    await cache_set(key, result, ttl=TTL_CONTACTS)
    return result


@router.post("/tenant/{tenant_id}/contacts", response_model=TenantContactResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_contact(
    tenant_id: int,
    payload: TenantContactCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantContactResponse:
    verify_tenant_access(tenant_id, current_user)

    existing = await db.scalar(select(TenantContact).where(
        TenantContact.tenant_id == tenant_id,
        TenantContact.contact_type == payload.contact_type.strip(),
    ))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Contact of type '{payload.contact_type}' already exists")

    contact = TenantContact(
        tenant_id=tenant_id, contact_type=payload.contact_type.strip(),
        first_name=payload.first_name.strip(), last_name=payload.last_name.strip(),
        position_title=payload.position_title, email=payload.email.lower(),
        phone=payload.phone, mobile=payload.mobile, is_active=payload.is_active,
    )
    db.add(contact)
    await db.flush()

    await log_audit(db=db, user_id=current_user["user_id"],
                    action="CREATE", table_name="tenant_contact",
                    record_id=str(contact.contact_id), new_values=payload.model_dump(), request=request)
    await db.commit()
    await db.refresh(contact)
    await cache_delete(f"tenant:{tenant_id}:contacts")
    return TenantContactResponse.model_validate(contact)


@router.put("/tenant/{tenant_id}/contacts/{contact_id}", response_model=TenantContactResponse)
async def update_tenant_contact(
    tenant_id: int,
    contact_id: int,
    payload: TenantContactUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantContactResponse:
    verify_tenant_access(tenant_id, current_user)
    contact = await db.scalar(select(TenantContact).where(
        TenantContact.contact_id == contact_id,
        TenantContact.tenant_id == tenant_id,
    ))
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    old_values = {c.name: getattr(contact, c.name) for c in contact.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(contact, field, val)

    await log_audit(db=db, user_id=current_user["user_id"],
                    action="UPDATE", table_name="tenant_contact", record_id=str(contact_id),
                    old_values=old_values, new_values=update_data, request=request)
    await db.commit()
    await db.refresh(contact)
    await cache_delete(f"tenant:{tenant_id}:contacts")
    return TenantContactResponse.model_validate(contact)


@router.delete("/tenant/{tenant_id}/contacts/{contact_id}", response_model=MessageResponse)
async def delete_tenant_contact(
    tenant_id: int,
    contact_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)

    contact = await db.scalar(select(TenantContact).where(
        TenantContact.contact_id == contact_id,
        TenantContact.tenant_id == tenant_id,
    ))
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    contact_type = contact.contact_type
    await db.delete(contact)
    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="DELETE", table_name="tenant_contact",
        record_id=str(contact_id),
        old_values={"contact_type": contact_type, "contact_id": contact_id},
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:contacts")
    return MessageResponse(message=f"Contact '{contact_type}' (id={contact_id}) deleted")
