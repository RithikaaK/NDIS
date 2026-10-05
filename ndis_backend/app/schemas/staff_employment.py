"""Staff Employment schemas — employment info, probation, contracts, job roles, exit process."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Employment Information ────────────────────────────────────────────────────

class EmploymentInformationCreate(BaseModel):
    employment_type: Optional[str] = Field(None, max_length=30)
    employment_status: Optional[str] = Field(None, max_length=30)
    pay_level: Optional[str] = Field(None, max_length=30)
    pay_point: Optional[str] = Field(None, max_length=30)
    position_title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    contracted_hours_per_week: Optional[float] = None
    reporting_manager_id: Optional[str] = Field(None, max_length=50)
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None
    notes: Optional[str] = None


class EmploymentInformationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employment_info_id: str
    staff_id: str
    tenant_id: int
    employment_type: Optional[str] = None
    employment_status: Optional[str] = None
    pay_level: Optional[str] = None
    pay_point: Optional[str] = None
    position_title: Optional[str] = None
    department: Optional[str] = None
    contracted_hours_per_week: Optional[float] = None
    reporting_manager_id: Optional[str] = None
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Probation ──────────────────────────────────────────────────────────

class StaffProbationCreate(BaseModel):
    probation_start_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    probation_status: Optional[str] = Field(None, max_length=30)
    reviewed_by: Optional[str] = Field(None, max_length=50)
    probation_review_notes: Optional[str] = Field(None, max_length=100)
    probation_extension_date: Optional[date] = None
    confirmed_as_permanent: Optional[bool] = None


class StaffProbationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    probation_id: str
    staff_id: str
    tenant_id: int
    probation_start_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    probation_status: Optional[str] = None
    reviewed_by: Optional[str] = None
    probation_review_notes: Optional[str] = None
    probation_extension_date: Optional[date] = None
    confirmed_as_permanent: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Contract ───────────────────────────────────────────────────────────

class StaffContractCreate(BaseModel):
    contract_type: Optional[str] = Field(None, max_length=30)
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_uploaded: Optional[bool] = None
    contract_file_path: Optional[str] = Field(None, max_length=255)
    contract_renewal_date: Optional[date] = None
    notice_period_timeline: Optional[str] = Field(None, max_length=30)
    schads_applicable: Optional[bool] = None


class StaffContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contract_id: str
    staff_id: str
    tenant_id: int
    contract_type: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_uploaded: Optional[bool] = None
    contract_file_path: Optional[str] = None
    contract_renewal_date: Optional[date] = None
    notice_period_timeline: Optional[str] = None
    schads_applicable: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Roles ──────────────────────────────────────────────────────────────

class StaffRolesCreate(BaseModel):
    role_name: Optional[str] = Field(None, max_length=100)
    role_level: Optional[str] = Field(None, max_length=50)
    role_description: Optional[str] = Field(None, max_length=500)
    role_start_date: Optional[date] = None
    role_end_date: Optional[date] = None
    is_active: bool = True


class StaffRolesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_role_id: str
    staff_id: str
    tenant_id: int
    role_name: Optional[str] = None
    role_level: Optional[str] = None
    role_description: Optional[str] = None
    role_start_date: Optional[date] = None
    role_end_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Exit Process ───────────────────────────────────────────────────────

class StaffExitProcessCreate(BaseModel):
    exit_type: Optional[str] = Field(None, max_length=30)
    resignation_date: Optional[date] = None
    last_working_date: Optional[date] = None
    exit_reason: Optional[str] = Field(None, max_length=100)
    notice_period_served: Optional[bool] = None
    exit_interview_date: Optional[date] = None
    handover_completed: Optional[bool] = None
    agreement_copy_uploaded: Optional[bool] = None
    agreement_file_path: Optional[str] = Field(None, max_length=255)
    access_revoked_date: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=30)


class StaffExitProcessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exit_process_id: str
    staff_id: str
    tenant_id: int
    exit_type: Optional[str] = None
    resignation_date: Optional[date] = None
    last_working_date: Optional[date] = None
    exit_reason: Optional[str] = None
    notice_period_served: Optional[bool] = None
    exit_interview_date: Optional[date] = None
    handover_completed: Optional[bool] = None
    agreement_copy_uploaded: Optional[bool] = None
    agreement_file_path: Optional[str] = None
    access_revoked_date: Optional[datetime] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
