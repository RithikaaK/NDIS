"""Tenant Documents router — tenant schema scoped."""
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models import TenantDocument
from app.routers.helpers import log_audit, verify_tenant_access
from app.schemas import MessageResponse
from app.schemas.tenant_document import (
    TenantDocumentCreate,
    TenantDocumentUpdate,
    TenantDocumentResponse,
)

router = APIRouter(tags=["Tenant Documents"])

TTL_DOCUMENTS = 300


@router.get("/tenant/{tenant_id}/documents", response_model=List[TenantDocumentResponse])
async def list_documents(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[TenantDocumentResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:documents"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    docs = (await db.scalars(
        select(TenantDocument)
        .where(
            TenantDocument.tenant_id == tenant_id,
            TenantDocument.is_deleted == False,  # noqa: E712
        )
        .order_by(TenantDocument.uploaded_at.desc())
    )).all()
    result = [TenantDocumentResponse.model_validate(d).model_dump(mode="json") for d in docs]
    await cache_set(key, result, ttl=TTL_DOCUMENTS)
    return result


@router.post(
    "/tenant/{tenant_id}/documents",
    response_model=TenantDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    tenant_id: int,
    payload: TenantDocumentCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantDocumentResponse:
    """Register a tenant document record.

    In production the file itself should be uploaded to object storage (S3/Azure Blob)
    before calling this endpoint. The file_path should be the resulting storage key/URL.
    """
    verify_tenant_access(tenant_id, current_user)

    doc = TenantDocument(
        tenant_id=tenant_id,
        document_category=payload.document_category.strip(),
        document_name=payload.document_name.strip(),
        file_path=payload.file_path.strip(),
        file_size_kb=payload.file_size_kb,
        mime_type=payload.mime_type,
        linked_to=payload.linked_to.strip() if payload.linked_to else None,
        expiry_date=payload.expiry_date,
        uploaded_by=current_user["user_id"],
        is_deleted=False,
    )
    db.add(doc)
    await db.flush()

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="CREATE", table_name="tenant_document",
        record_id=str(doc.document_id),
        new_values={
            "document_category": doc.document_category,
            "document_name": doc.document_name,
            "linked_to": doc.linked_to,
            "file_path": doc.file_path,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(doc)
    await cache_delete(f"tenant:{tenant_id}:documents")
    return TenantDocumentResponse.model_validate(doc)


@router.put("/tenant/{tenant_id}/documents/{document_id}", response_model=TenantDocumentResponse)
async def update_document(
    tenant_id: int,
    document_id: int,
    payload: TenantDocumentUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantDocumentResponse:
    """Update document metadata (category, name, linked_to, expiry_date)."""
    verify_tenant_access(tenant_id, current_user)

    doc = await db.scalar(select(TenantDocument).where(
        TenantDocument.document_id == document_id,
        TenantDocument.tenant_id == tenant_id,
        TenantDocument.is_deleted == False,  # noqa: E712
    ))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    old_values = {
        "document_category": doc.document_category,
        "document_name": doc.document_name,
        "linked_to": doc.linked_to,
        "expiry_date": str(doc.expiry_date) if doc.expiry_date else None,
    }
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="UPDATE", table_name="tenant_document",
        record_id=str(document_id),
        old_values=old_values, new_values=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(doc)
    await cache_delete(f"tenant:{tenant_id}:documents")
    return TenantDocumentResponse.model_validate(doc)


@router.delete("/tenant/{tenant_id}/documents/{document_id}", response_model=MessageResponse)
async def delete_document(
    tenant_id: int,
    document_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    """Soft-delete a tenant document record."""
    verify_tenant_access(tenant_id, current_user)

    doc = await db.scalar(select(TenantDocument).where(
        TenantDocument.document_id == document_id,
        TenantDocument.tenant_id == tenant_id,
        TenantDocument.is_deleted == False,  # noqa: E712
    ))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc_name = doc.document_name
    doc.is_deleted = True
    doc.deleted_at = datetime.now(timezone.utc)

    await log_audit(
        db=db, user_id=current_user["user_id"],
        action="SOFT_DELETE", table_name="tenant_document",
        record_id=str(document_id),
        old_values={"document_name": doc_name, "document_category": doc.document_category},
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:documents")
    return MessageResponse(message=f"Document '{doc_name}' deleted")
