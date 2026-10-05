"""Staff Profile router — profiles, personal info, contact info, identification, emergency contacts, preferences."""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db, get_tenant_session
from app.models import AppUser
from app.models.staff_profile import StaffProfile
from app.models.staff_personal_info import StaffPersonalInfo
from app.models.staff_contact_info import StaffContactInfo
from app.models.staff_identification import StaffIdentification
from app.models.staff_preferences import StaffPreferences
from app.models.staff_emergency_contact import StaffEmergencyContact
from app.models.employment_information import EmploymentInformation
from app.models.staff_probation import StaffProbation
from app.models.staff_contract import StaffContract
from app.models.staff_roles import StaffRoles
from app.models.staff_exit_process import StaffExitProcess
from app.models.staff_qualification import StaffQualification
from app.models.staff_certification import StaffCertification
from app.models.staff_availability import StaffAvailability
from app.models.staff_document_repository import StaffDocumentRepository
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas.staff_profile import (
    StaffProfileCreate, StaffProfileUpdate, StaffProfileResponse,
    StaffPersonalInfoCreate, StaffPersonalInfoResponse,
    StaffContactInfoCreate, StaffContactInfoResponse,
    StaffIdentificationCreate, StaffIdentificationResponse,
    StaffPreferencesCreate, StaffPreferencesResponse,
    StaffEmergencyContactCreate, StaffEmergencyContactResponse,
)
from app.schemas.staff_employment import (
    EmploymentInformationResponse,
    StaffProbationResponse,
    StaffContractResponse,
    StaffRolesResponse,
    StaffExitProcessResponse,
)
from app.schemas.staff_compliance import (
    StaffQualificationResponse,
    StaffCertificationResponse,
)
from app.schemas.staff_availability import StaffAvailabilityResponse
from app.schemas.staff_documents import StaffDocumentResponse
from app.schemas.staff_detail import StaffDetailResponse

router = APIRouter(tags=["Staff — Profiles"])

BASE = "/tenant/{tenant_id}/staff"


def _uid() -> str:
    return str(uuid.uuid4())


def _short_id() -> str:
    return str(uuid.uuid4()).replace("-", "")[:20]


# ═══════════════════════════════════════════════════════════════════════════════
# STAFF PROFILES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE, response_model=List[StaffProfileResponse])
async def list_staff(
    tenant_id: int,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")

    q = select(StaffProfile).where(StaffProfile.is_deleted == False)  # noqa: E712
    if status:
        q = q.where(StaffProfile.status == status)
    q = q.order_by(StaffProfile.last_name, StaffProfile.first_name)
    rows = (await db.scalars(q)).all()
    return [StaffProfileResponse.model_validate(r) for r in rows]


@router.post(BASE, response_model=StaffProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    tenant_id: int,
    payload: StaffProfileCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:create")

    staff = StaffProfile(
        staff_id=payload.staff_id or _uid(),
        tenant_id=tenant_id,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        photo=payload.photo,
        work_email=payload.work_email,
        status=payload.status,
        created_by=current_user.get("user_id"),
    )
    db.add(staff)
    await db.flush()
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_profile", staff.staff_id,
                    new_values={"first_name": staff.first_name, "last_name": staff.last_name}, request=request)
    await db.commit()
    await db.refresh(staff)
    return StaffProfileResponse.model_validate(staff)


@router.get(BASE + "/{staff_id}", response_model=StaffDetailResponse)
async def get_staff(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")

    profile = await db.scalar(select(StaffProfile).where(
        StaffProfile.staff_id == staff_id, StaffProfile.is_deleted == False  # noqa: E712
    ))
    if not profile:
        raise HTTPException(status_code=404, detail="Staff member not found")

    personal = await db.scalar(select(StaffPersonalInfo).where(
        StaffPersonalInfo.staff_id == staff_id, StaffPersonalInfo.is_deleted == False))  # noqa: E712
    contact = await db.scalar(select(StaffContactInfo).where(
        StaffContactInfo.staff_id == staff_id, StaffContactInfo.is_deleted == False))  # noqa: E712
    employment = await db.scalar(select(EmploymentInformation).where(
        EmploymentInformation.staff_id == staff_id, EmploymentInformation.is_deleted == False))  # noqa: E712
    probation = await db.scalar(select(StaffProbation).where(
        StaffProbation.staff_id == staff_id, StaffProbation.is_deleted == False))  # noqa: E712
    contract = await db.scalar(select(StaffContract).where(
        StaffContract.staff_id == staff_id, StaffContract.is_deleted == False))  # noqa: E712
    preferences = await db.scalar(select(StaffPreferences).where(
        StaffPreferences.staff_id == staff_id, StaffPreferences.is_deleted == False))  # noqa: E712
    exit_proc = await db.scalar(select(StaffExitProcess).where(
        StaffExitProcess.staff_id == staff_id, StaffExitProcess.is_deleted == False))  # noqa: E712

    roles = (await db.scalars(select(StaffRoles).where(
        StaffRoles.staff_id == staff_id, StaffRoles.is_deleted == False))).all()  # noqa: E712
    identifications = (await db.scalars(select(StaffIdentification).where(
        StaffIdentification.staff_id == staff_id, StaffIdentification.is_deleted == False))).all()  # noqa: E712
    emergency_contacts = (await db.scalars(select(StaffEmergencyContact).where(
        StaffEmergencyContact.staff_id == staff_id, StaffEmergencyContact.is_deleted == False))).all()  # noqa: E712
    qualifications = (await db.scalars(select(StaffQualification).where(
        StaffQualification.staff_id == staff_id, StaffQualification.is_deleted == False))).all()  # noqa: E712
    certifications = (await db.scalars(select(StaffCertification).where(
        StaffCertification.staff_id == staff_id, StaffCertification.is_deleted == False))).all()  # noqa: E712
    availability = (await db.scalars(select(StaffAvailability).where(
        StaffAvailability.staff_id == staff_id, StaffAvailability.is_deleted == False))).all()  # noqa: E712
    documents = (await db.scalars(select(StaffDocumentRepository).where(
        StaffDocumentRepository.staff_id == staff_id, StaffDocumentRepository.is_deleted == False))).all()  # noqa: E712

    return StaffDetailResponse(
        profile=StaffProfileResponse.model_validate(profile),
        personal_info=StaffPersonalInfoResponse.model_validate(personal) if personal else None,
        contact_info=StaffContactInfoResponse.model_validate(contact) if contact else None,
        employment=EmploymentInformationResponse.model_validate(employment) if employment else None,
        probation=StaffProbationResponse.model_validate(probation) if probation else None,
        contract=StaffContractResponse.model_validate(contract) if contract else None,
        preferences=StaffPreferencesResponse.model_validate(preferences) if preferences else None,
        exit_process=StaffExitProcessResponse.model_validate(exit_proc) if exit_proc else None,
        roles=[StaffRolesResponse.model_validate(r) for r in roles],
        identifications=[StaffIdentificationResponse.model_validate(r) for r in identifications],
        emergency_contacts=[StaffEmergencyContactResponse.model_validate(r) for r in emergency_contacts],
        qualifications=[StaffQualificationResponse.model_validate(r) for r in qualifications],
        certifications=[StaffCertificationResponse.model_validate(r) for r in certifications],
        availability=[StaffAvailabilityResponse.model_validate(r) for r in availability],
        documents=[StaffDocumentResponse.model_validate(r) for r in documents],
    )


@router.patch(BASE + "/{staff_id}", response_model=StaffProfileResponse)
async def update_staff(
    tenant_id: int,
    staff_id: str,
    payload: StaffProfileUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
    common_db: AsyncSession = Depends(get_db),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")

    staff = await db.scalar(select(StaffProfile).where(
        StaffProfile.staff_id == staff_id, StaffProfile.is_deleted == False))  # noqa: E712
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    old = {"status": staff.status}
    changes = payload.model_dump(exclude_unset=True)
    for field, val in changes.items():
        setattr(staff, field, val)
    staff.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_profile", staff_id,
                    old_values=old, new_values=changes, request=request)

    # Sync name / email changes back to the linked AppUser in ndis_common
    if staff.user_id and any(k in changes for k in ("first_name", "last_name", "work_email")):
        app_user = await common_db.scalar(
            select(AppUser).where(AppUser.user_id == staff.user_id, AppUser.is_deleted == False)  # noqa: E712
        )
        if app_user:
            if "first_name" in changes and changes["first_name"]:
                app_user.first_name = changes["first_name"].strip()
            if "last_name" in changes and changes["last_name"]:
                app_user.last_name = changes["last_name"].strip()
            if "work_email" in changes and changes["work_email"]:
                app_user.email = changes["work_email"].lower().strip()
            app_user.updated_by = current_user.get("user_id")
        await common_db.commit()

    await db.commit()
    await db.refresh(staff)
    return StaffProfileResponse.model_validate(staff)


@router.delete(BASE + "/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    tenant_id: int,
    staff_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:delete")

    staff = await db.scalar(select(StaffProfile).where(
        StaffProfile.staff_id == staff_id, StaffProfile.is_deleted == False))  # noqa: E712
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    staff.is_deleted = True
    staff.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_profile", staff_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONAL INFO
# ═══════════════════════════════════════════════════════════════════════════════

@router.put(BASE + "/{staff_id}/personal-info", response_model=StaffPersonalInfoResponse)
async def upsert_personal_info(
    tenant_id: int,
    staff_id: str,
    payload: StaffPersonalInfoCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")

    record = await db.scalar(select(StaffPersonalInfo).where(
        StaffPersonalInfo.staff_id == staff_id, StaffPersonalInfo.is_deleted == False))  # noqa: E712
    if record:
        for f, v in payload.model_dump(exclude_unset=True).items():
            setattr(record, f, v)
        record.updated_by = current_user.get("user_id")
        action = "UPDATE"
    else:
        record = StaffPersonalInfo(
            personal_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
            **payload.model_dump(), created_by=current_user.get("user_id"),
        )
        db.add(record)
        action = "CREATE"
    await log_audit(db, current_user.get("user_id"), action, "staff_personal_info", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffPersonalInfoResponse.model_validate(record)


@router.get(BASE + "/{staff_id}/personal-info", response_model=Optional[StaffPersonalInfoResponse])
async def get_personal_info(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    record = await db.scalar(select(StaffPersonalInfo).where(
        StaffPersonalInfo.staff_id == staff_id, StaffPersonalInfo.is_deleted == False))  # noqa: E712
    return StaffPersonalInfoResponse.model_validate(record) if record else None


# ═══════════════════════════════════════════════════════════════════════════════
# CONTACT INFO
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/contact-info", response_model=Optional[StaffContactInfoResponse])
async def get_contact_info(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    record = await db.scalar(select(StaffContactInfo).where(
        StaffContactInfo.staff_id == staff_id, StaffContactInfo.is_deleted == False))  # noqa: E712
    return StaffContactInfoResponse.model_validate(record) if record else None


@router.put(BASE + "/{staff_id}/contact-info", response_model=StaffContactInfoResponse)
async def upsert_contact_info(
    tenant_id: int,
    staff_id: str,
    payload: StaffContactInfoCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")

    record = await db.scalar(select(StaffContactInfo).where(
        StaffContactInfo.staff_id == staff_id, StaffContactInfo.is_deleted == False))  # noqa: E712
    if record:
        for f, v in payload.model_dump(exclude_unset=True).items():
            setattr(record, f, v)
        record.updated_by = current_user.get("user_id")
    else:
        record = StaffContactInfo(
            staff_contact_id=_uid(), tenant_id=str(tenant_id), staff_id=staff_id,
            **payload.model_dump(), created_by=current_user.get("user_id"),
        )
        db.add(record)
    await log_audit(db, current_user.get("user_id"), "UPSERT", "staff_contact_info", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffContactInfoResponse.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/identifications", response_model=List[StaffIdentificationResponse])
async def list_identifications(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffIdentification).where(
        StaffIdentification.staff_id == staff_id,
        StaffIdentification.is_deleted == False))).all()  # noqa: E712
    return [StaffIdentificationResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/identifications", response_model=StaffIdentificationResponse,
             status_code=status.HTTP_201_CREATED)
async def add_identification(
    tenant_id: int,
    staff_id: str,
    payload: StaffIdentificationCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = StaffIdentification(
        staff_iden_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_identification", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffIdentificationResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/identifications/{iden_id}", response_model=StaffIdentificationResponse)
async def update_identification(
    tenant_id: int,
    staff_id: str,
    iden_id: str,
    payload: StaffIdentificationCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffIdentification).where(
        StaffIdentification.staff_iden_id == iden_id,
        StaffIdentification.staff_id == staff_id,
        StaffIdentification.is_deleted == False,  # noqa: E712
    ))
    if not record:
        raise HTTPException(status_code=404, detail="Identity document not found")
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, val)
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_identification", iden_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffIdentificationResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/identifications/{iden_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_identification(
    tenant_id: int,
    staff_id: str,
    iden_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffIdentification).where(
        StaffIdentification.staff_iden_id == iden_id,
        StaffIdentification.staff_id == staff_id,
        StaffIdentification.is_deleted == False,  # noqa: E712
    ))
    if not record:
        raise HTTPException(status_code=404, detail="Identity document not found")
    record.is_deleted = True
    record.updated_by = current_user.get("user_id")
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_identification", iden_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# EMERGENCY CONTACTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/emergency-contacts", response_model=List[StaffEmergencyContactResponse])
async def list_emergency_contacts(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    rows = (await db.scalars(select(StaffEmergencyContact).where(
        StaffEmergencyContact.staff_id == staff_id,
        StaffEmergencyContact.is_deleted == False))).all()  # noqa: E712
    return [StaffEmergencyContactResponse.model_validate(r) for r in rows]


@router.post(BASE + "/{staff_id}/emergency-contacts", response_model=StaffEmergencyContactResponse,
             status_code=status.HTTP_201_CREATED)
async def add_emergency_contact(
    tenant_id: int,
    staff_id: str,
    payload: StaffEmergencyContactCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = StaffEmergencyContact(
        emergency_contact_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
        **payload.model_dump(), created_by=current_user.get("user_id"),
    )
    db.add(record)
    await log_audit(db, current_user.get("user_id"), "CREATE", "staff_emergency_contact", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffEmergencyContactResponse.model_validate(record)


@router.patch(BASE + "/{staff_id}/emergency-contacts/{contact_id}", response_model=StaffEmergencyContactResponse)
async def update_emergency_contact(
    tenant_id: int,
    staff_id: str,
    contact_id: str,
    payload: StaffEmergencyContactCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffEmergencyContact).where(
        StaffEmergencyContact.emergency_contact_id == contact_id,
        StaffEmergencyContact.staff_id == staff_id,
        StaffEmergencyContact.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Emergency contact not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await log_audit(db, current_user.get("user_id"), "UPDATE", "staff_emergency_contact", contact_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffEmergencyContactResponse.model_validate(record)


@router.delete(BASE + "/{staff_id}/emergency-contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_emergency_contact(
    tenant_id: int,
    staff_id: str,
    contact_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffEmergencyContact).where(
        StaffEmergencyContact.emergency_contact_id == contact_id,
        StaffEmergencyContact.staff_id == staff_id,
        StaffEmergencyContact.is_deleted == False))  # noqa: E712
    if not record:
        raise HTTPException(status_code=404, detail="Emergency contact not found")
    record.is_deleted = True
    await log_audit(db, current_user.get("user_id"), "DELETE", "staff_emergency_contact", contact_id, request=request)
    await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# PREFERENCES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(BASE + "/{staff_id}/preferences", response_model=Optional[StaffPreferencesResponse])
async def get_preferences(
    tenant_id: int,
    staff_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:view")
    record = await db.scalar(select(StaffPreferences).where(
        StaffPreferences.staff_id == staff_id, StaffPreferences.is_deleted == False))  # noqa: E712
    return StaffPreferencesResponse.model_validate(record) if record else None


@router.put(BASE + "/{staff_id}/preferences", response_model=StaffPreferencesResponse)
async def upsert_preferences(
    tenant_id: int,
    staff_id: str,
    payload: StaffPreferencesCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "staff:edit")
    record = await db.scalar(select(StaffPreferences).where(
        StaffPreferences.staff_id == staff_id, StaffPreferences.is_deleted == False))  # noqa: E712
    if record:
        for f, v in payload.model_dump(exclude_unset=True).items():
            setattr(record, f, v)
        record.updated_by = current_user.get("user_id")
    else:
        record = StaffPreferences(
            staff_pref_id=_uid(), tenant_id=tenant_id, staff_id=staff_id,
            **payload.model_dump(), created_by=current_user.get("user_id"),
        )
        db.add(record)
    await log_audit(db, current_user.get("user_id"), "UPSERT", "staff_preferences", staff_id, request=request)
    await db.commit()
    await db.refresh(record)
    return StaffPreferencesResponse.model_validate(record)
