"""Staff Compliance schemas — qualifications and certifications (master catalogues + staff records)."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Qualification (master catalogue) ────────────────────────────────────────

class QualificationCreate(BaseModel):
    qualification_id: str = Field(..., max_length=20)
    qualification_type: str = Field(..., max_length=150)
    qualification_level: Optional[str] = Field(None, max_length=50)
    qualification_description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class QualificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    qualification_id: str
    qualification_type: str
    qualification_level: Optional[str] = None
    qualification_description: Optional[str] = None
    is_active: bool
    created_at: datetime


# ─── Staff Qualification ──────────────────────────────────────────────────────

class StaffQualificationCreate(BaseModel):
    qualification_id: str = Field(..., max_length=20)
    issuing_institution: Optional[str] = Field(None, max_length=100)
    year_commenced: Optional[int] = None
    year_completed: Optional[int] = None
    expiry_date: Optional[date] = None
    document_url: Optional[str] = None
    certificate_uploaded: Optional[bool] = None
    verification_status: Optional[str] = Field(None, max_length=30)
    verification_date: Optional[date] = None
    verified_by: Optional[str] = Field(None, max_length=50)
    verify_remarks: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=30)


class StaffQualificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_qualification_id: str
    staff_id: str
    tenant_id: int
    qualification_id: str
    issuing_institution: Optional[str] = None
    year_commenced: Optional[int] = None
    year_completed: Optional[int] = None
    expiry_date: Optional[date] = None
    document_url: Optional[str] = None
    certificate_uploaded: Optional[bool] = None
    verification_status: Optional[str] = None
    verification_date: Optional[date] = None
    verified_by: Optional[str] = None
    verify_remarks: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Certification (master catalogue) ────────────────────────────────────────

class CertificationCreate(BaseModel):
    certification_id: str = Field(..., max_length=20)
    certification_name: str = Field(..., max_length=150)
    certification_category: Optional[str] = Field(None, max_length=50)
    certification_description: Optional[str] = Field(None, max_length=500)
    expiry_applicability: Optional[bool] = None
    validity_period_months: Optional[int] = None
    renewal_required: Optional[bool] = None
    is_active: bool = True


class CertificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    certification_id: str
    certification_name: str
    certification_category: Optional[str] = None
    certification_description: Optional[str] = None
    expiry_applicability: Optional[bool] = None
    validity_period_months: Optional[int] = None
    renewal_required: Optional[bool] = None
    is_active: bool
    created_at: datetime


# ─── Staff Certification ──────────────────────────────────────────────────────

class StaffCertificationCreate(BaseModel):
    certification_id: str = Field(..., max_length=20)
    certification_status: Optional[str] = Field(None, max_length=30)
    issuing_provider: Optional[str] = Field(None, max_length=50)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    document_url: Optional[str] = None
    certificate_uploaded: Optional[bool] = None
    verification_status: Optional[str] = Field(None, max_length=30)
    verified_by: Optional[str] = Field(None, max_length=50)
    verified_date: Optional[date] = None


class StaffCertificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_certification_id: str
    staff_id: str
    tenant_id: int
    certification_id: str
    certification_status: Optional[str] = None
    issuing_provider: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    document_url: Optional[str] = None
    certificate_uploaded: Optional[bool] = None
    verification_status: Optional[str] = None
    verified_by: Optional[str] = None
    verified_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
