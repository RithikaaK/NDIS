"""Staff Documents router — staff document repository."""
import os
import uuid
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models.staff_document_repository import StaffDocumentRepository
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_documents import StaffDocumentResponse

router = APIRouter(tags=["Staff — Documents"])

BASE = "/tenant/{tenant_id}/staff"

# ── Storage config ─────────────────────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "staff", "documents")
ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xlsx", ".xls", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _short_id() -> str:
    return str(uuid.uuid4()).replace("-", "")[:20]


# ═══════════════════════════════════════════════════════════════════════════════
# LIST DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/documents", response_model=List[StaffDocumentResponse])
async def list_documents(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """Return all non-deleted documents for a staff member (tenant-isolated)."""
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffDocumentRepository).where(
        StaffDocumentRepository.staff_id == staff_id,
        StaffDocumentRepository.tenant_id == tenant_id,
        StaffDocumentRepository.is_deleted == False))).all()  # noqa: E712
    return [StaffDocumentResponse.model_validate(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD / CREATE DOCUMENT  (multipart/form-data)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    BASE + "/{staff_id}/documents",
    response_model=StaffDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    tenant_id: int,
    staff_id: str,
    request: Request,
    # ── file (required) ──────────────────────────────────────────────────
    file: UploadFile = File(..., description="Document file (PDF, Word, image, etc.)"),
    # ── metadata fields ──────────────────────────────────────────────────
    document_type: str = Form(..., description="Document type (e.g. ID Document, Contract)"),
    document_name: str = Form(..., description="Human-readable document name"),
    document_status: str = Form("Active", description="Active | Pending | Expired | Rejected | Archived"),
    document_description: Optional[str] = Form(None, description="Optional free-text description"),
    expiry_date: Optional[str] = Form(None, description="ISO date string YYYY-MM-DD, optional"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """Upload a document file together with its metadata.

    Accepts multipart/form-data with these fields:
      • file            – binary file (required)
      • document_type   – required
      • document_name   – required
      • document_status – defaults to 'Active'
      • document_description – optional
      • expiry_date     – optional YYYY-MM-DD string

    Validates:
      • Tenant isolation (JWT tenant_id == URL tenant_id)
      • Permission: staff:documents
      • File extension must be in ALLOWED_EXTS
      • File size ≤ 10 MB

    Stores file under uploads/staff/documents/<unique_name>.<ext>
    and records file_path + file_url on the database row.
    """
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:documents")

    # ── Validate file extension ────────────────────────────────────────────
    original_name = file.filename or "untitled"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"File type '{ext or '(none)'}' is not allowed. "
                f"Accepted: {', '.join(sorted(ALLOWED_EXTS))}"
            ),
        )

    # ── Read & validate file size ──────────────────────────────────────────
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the 10 MB limit ({len(content) // (1024*1024)} MB uploaded).",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    # ── Parse optional expiry date ─────────────────────────────────────────
    parsed_expiry: Optional[date] = None
    if expiry_date and expiry_date.strip():
        try:
            parsed_expiry = date.fromisoformat(expiry_date.strip())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid expiry_date '{expiry_date}'. Expected format: YYYY-MM-DD.",
            )

    # ── Save file to disk ──────────────────────────────────────────────────
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_fname = f"{_short_id()}{ext}"
    dest = os.path.join(UPLOAD_DIR, unique_fname)
    with open(dest, "wb") as fout:
        fout.write(content)

    relative_path = f"uploads/staff/documents/{unique_fname}"
    file_url = f"/{relative_path}"

    # ── Persist database record ────────────────────────────────────────────
    user_id = current_user.get("user_id")
    doc_id = _short_id()

    record = StaffDocumentRepository(
        document_id=doc_id,
        tenant_id=tenant_id,
        staff_id=staff_id,
        document_type=document_type.strip(),
        document_name=document_name.strip(),
        document_description=document_description.strip() if document_description else None,
        document_status=document_status,
        expiry_date=parsed_expiry,
        file_path=relative_path,
        file_url=file_url,
        file_format=ext.lstrip("."),
        upload_date=date.today(),
        uploaded_by=user_id,
        created_by=user_id,
        is_active=True,
        is_deleted=False,
    )
    db.add(record)
    await log_audit(
        db, user_id, "CREATE", "staff_document_repository", doc_id,
        new_values={"staff_id": staff_id, "document_name": document_name},
        request=request,
    )
    await db.commit()
    await db.refresh(record)
    return StaffDocumentResponse.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE DOCUMENT  (soft-delete)
# ═══════════════════════════════════════════════════════════════════════════════

@router.delete(
    BASE + "/{staff_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    tenant_id: int,
    staff_id: str,
    document_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """Soft-delete a document record (does not remove the file from disk)."""
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:documents")
    record = await db.scalar(select(StaffDocumentRepository).where(
        StaffDocumentRepository.document_id == document_id,
        StaffDocumentRepository.staff_id == staff_id,
        StaffDocumentRepository.tenant_id == tenant_id,
        StaffDocumentRepository.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(
        db, current_user.get("user_id"), "DELETE",
        "staff_document_repository", document_id,
        old_values={"staff_id": staff_id, "document_name": record.document_name},
        request=request,
    )
    await db.commit()

# ═══════════════════════════════════════════════════════════════════════════════
# UPDATE DOCUMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.patch(
    BASE + "/{staff_id}/documents/{document_id}",
    response_model=StaffDocumentResponse,
)
async def update_document(
    tenant_id: int,
    staff_id: str,
    document_id: str,
    request: Request,
    file: Optional[UploadFile] = File(None, description="Optional new document file"),
    document_type: Optional[str] = Form(None),
    document_name: Optional[str] = Form(None),
    document_status: Optional[str] = Form(None),
    document_description: Optional[str] = Form(None),
    expiry_date: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """Update a document's metadata and/or replace the physical file."""
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:documents")

    record = await db.scalar(select(StaffDocumentRepository).where(
        StaffDocumentRepository.document_id == document_id,
        StaffDocumentRepository.staff_id == staff_id,
        StaffDocumentRepository.tenant_id == tenant_id,
        StaffDocumentRepository.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    user_id = current_user.get("user_id")

    # ── Snapshot "before" values for the fields this endpoint can change,
    # so the audit log can show exactly what changed (not just that an
    # update happened).
    before = {
        "document_type": record.document_type,
        "document_name": record.document_name,
        "document_status": record.document_status,
        "document_description": record.document_description,
        "expiry_date": record.expiry_date.isoformat() if record.expiry_date else None,
        "file_format": record.file_format,
    }

    if file and file.filename:
        original_name = file.filename
        ext = os.path.splitext(original_name)[1].lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File type '{ext or '(none)'}' is not allowed. Accepted: {', '.join(sorted(ALLOWED_EXTS))}",
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds the 10 MB limit.")
        if len(content) == 0:
            raise HTTPException(status_code=422, detail="Uploaded file is empty.")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        unique_fname = f"{_short_id()}{ext}"
        dest = os.path.join(UPLOAD_DIR, unique_fname)
        with open(dest, "wb") as fout:
            fout.write(content)

        relative_path = f"uploads/staff/documents/{unique_fname}"
        record.file_path = relative_path
        record.file_url = f"/{relative_path}"
        record.file_format = ext.lstrip(".")
        record.upload_date = date.today()
        record.uploaded_by = user_id

    if document_type is not None:
        record.document_type = document_type.strip()
    if document_name is not None:
        record.document_name = document_name.strip()
    if document_status is not None:
        record.document_status = document_status.strip()
    if document_description is not None:
        record.document_description = document_description.strip()

    if expiry_date is not None:
        if not expiry_date.strip() or expiry_date.strip().lower() == "null":
            record.expiry_date = None
        else:
            try:
                record.expiry_date = date.fromisoformat(expiry_date.strip())
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid expiry_date format.")

    record.updated_by = user_id

    # ── Diff "after" values against the snapshot and log only what changed,
    # so the audit trail reads as a real change list rather than a blank
    # "UPDATE" entry.
    after = {
        "document_type": record.document_type,
        "document_name": record.document_name,
        "document_status": record.document_status,
        "document_description": record.document_description,
        "expiry_date": record.expiry_date.isoformat() if record.expiry_date else None,
        "file_format": record.file_format,
    }
    changed_keys = [k for k in before if before[k] != after[k]]
    old_changed = {k: before[k] for k in changed_keys}
    new_changed = {k: after[k] for k in changed_keys}
    old_changed["staff_id"] = staff_id
    new_changed["staff_id"] = staff_id

    await log_audit(
        db, user_id, "UPDATE", "staff_document_repository", document_id,
        old_values=old_changed,
        new_values=new_changed,
        request=request,
    )
    await db.commit()
    await db.refresh(record)
    return StaffDocumentResponse.model_validate(record)
