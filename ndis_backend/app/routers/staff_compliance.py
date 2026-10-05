"""Staff Compliance router — qualification & certification catalogues + staff mappings."""
import os
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "staff")
ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}

from app.core.security import get_current_user
from app.database import get_db, get_tenant_session
from app.models.qualification import Qualification
from app.models.staff_qualification import StaffQualification
from app.models.certification import Certification
from app.models.staff_certification import StaffCertification
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_compliance import (
    QualificationCreate, QualificationResponse,
    StaffQualificationCreate, StaffQualificationResponse,
    CertificationCreate, CertificationResponse,
    StaffCertificationCreate, StaffCertificationResponse,
)

router = APIRouter(tags=["Staff — Compliance"])

BASE = "/tenant/{tenant_id}/staff"


def _short_id() -> str:
    return str(uuid.uuid4()).replace("-", "")[:20]


# ═══════════════════════════════════════════════════════════════════════════════
# QUALIFICATIONS (master catalogue — uses common DB)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/qualifications", response_model=List[QualificationResponse])
async def list_qualifications(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.scalars(
        select(Qualification).where(Qualification.is_deleted == False, Qualification.is_active == True)  # noqa: E712
        .order_by(Qualification.qualification_type)
    )).all()
    return [QualificationResponse.model_validate(r) for r in rows]


@router.post("/qualifications", response_model=QualificationResponse, status_code=status.HTTP_201_CREATED)
async def create_qualification(
    payload: QualificationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = Qualification(**payload.model_dump(), created_by=current_user.get("user_id"))
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return QualificationResponse.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# STAFF QUALIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/qualifications", response_model=List[StaffQualificationResponse])
async def list_staff_qualifications(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffQualification).where(
        StaffQualification.staff_id == staff_id,
        StaffQualification.is_deleted == False))).all()  # noqa: E712
    return [StaffQualificationResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/qualifications", response_model=StaffQualificationResponse,
             status_code=status.HTTP_201_CREATED)
async def add_staff_qualification(
    tenant_id: int,
    staff_id: str,
    payload: StaffQualificationCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = StaffQualification(
        staff_qualification_id=_short_id(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_qualification", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffQualificationResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/qualifications/{qual_id}", response_model=StaffQualificationResponse)
async def update_staff_qualification(
    tenant_id: int, staff_id: str, qual_id: str,
    payload: StaffQualificationCreate, request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffQualification).where(
        StaffQualification.staff_qualification_id == qual_id,
        StaffQualification.staff_id == staff_id,
        StaffQualification.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Qualification not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_qualification", qual_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffQualificationResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/qualifications/{qual_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff_qualification(
    tenant_id: int, staff_id: str, qual_id: str, request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffQualification).where(
        StaffQualification.staff_qualification_id == qual_id,
        StaffQualification.staff_id == staff_id,
        StaffQualification.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Qualification not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_qualification", qual_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# CERTIFICATIONS (master catalogue)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/certifications", response_model=List[CertificationResponse])
async def list_certifications(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.scalars(
        select(Certification).where(Certification.is_deleted == False, Certification.is_active == True)  # noqa: E712
        .order_by(Certification.certification_name)
    )).all()
    return [CertificationResponse.model_validate(r) for r in rows]


@router.post("/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def create_certification(
    payload: CertificationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = Certification(**payload.model_dump(), created_by=current_user.get("user_id"))
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return CertificationResponse.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# STAFF CERTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/certifications", response_model=List[StaffCertificationResponse])
async def list_staff_certifications(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffCertification).where(
        StaffCertification.staff_id == staff_id,
        StaffCertification.is_deleted == False))).all()  # noqa: E712
    return [StaffCertificationResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/certifications", response_model=StaffCertificationResponse,
             status_code=status.HTTP_201_CREATED)
async def add_staff_certification(
    tenant_id: int,
    staff_id: str,
    payload: StaffCertificationCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = StaffCertification(
        staff_certification_id=_short_id(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_certification", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffCertificationResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/certifications/{cert_id}", response_model=StaffCertificationResponse)
async def update_staff_certification(
    tenant_id: int, staff_id: str, cert_id: str,
    payload: StaffCertificationCreate, request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffCertification).where(
        StaffCertification.staff_certification_id == cert_id,
        StaffCertification.staff_id == staff_id,
        StaffCertification.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Certification not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, f, v)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_certification", cert_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffCertificationResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/certifications/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff_certification(
    tenant_id: int, staff_id: str, cert_id: str, request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffCertification).where(
        StaffCertification.staff_certification_id == cert_id,
        StaffCertification.staff_id == staff_id,
        StaffCertification.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Certification not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_certification", cert_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# FILE UPLOAD  (shared for quals & certs)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(BASE + "/{staff_id}/upload-document")
async def upload_compliance_document(
    tenant_id: int,
    staff_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """Upload a document for a staff qualification or certification.
    Returns {"url": "/uploads/staff/<filename>", "original_name": "<original>"}
    """
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    fname = f"{_short_id()}{ext}"
    dest = os.path.join(UPLOAD_DIR, fname)

    content = await file.read()
    with open(dest, "wb") as out:
        out.write(content)

    return {"url": f"/uploads/staff/{fname}", "original_name": file.filename}
