"""Branch schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

BRANCH_TYPES = [
    "Head Office",
    "Branch Office",
    "Service Centre",
    "Community Hub",
    "Day Programme",
    "Respite House",
    "Administrative Office",
    "Other",
]

BRANCH_STATUSES = ["Active", "Inactive", "Temporarily Closed", "Permanently Closed"]

AU_TIMEZONES = [
    "Australia/Sydney",
    "Australia/Melbourne",
    "Australia/Brisbane",
    "Australia/Adelaide",
    "Australia/Perth",
    "Australia/Darwin",
    "Australia/Hobart",
    "Australia/Lord_Howe",
]


class BranchCreate(BaseModel):
    branch_code: str = Field(..., min_length=2, max_length=50)
    branch_name: str = Field(..., min_length=2, max_length=255)
    branch_type: Optional[str] = Field(None, max_length=100)
    parent_branch_id: Optional[int] = None
    branch_status: Optional[str] = Field("Active", max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    suburb: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, max_length=10)
    postcode: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=100)
    operating_hours: Optional[str] = None
    facilities: Optional[str] = None
    notes: Optional[str] = None
    is_head_office: bool = False
    is_active: bool = True


class BranchUpdate(BaseModel):
    branch_name: Optional[str] = Field(None, max_length=255)
    branch_type: Optional[str] = Field(None, max_length=100)
    parent_branch_id: Optional[int] = None
    branch_status: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    suburb: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, max_length=10)
    postcode: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=100)
    operating_hours: Optional[str] = None
    facilities: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_title: Optional[str] = Field(None, max_length=150)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_mobile: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=255)
    is_head_office: Optional[bool] = None


class BranchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    branch_id: int
    branch_code: str
    branch_name: str
    branch_type: Optional[str] = None
    parent_branch_id: Optional[int] = None
    branch_status: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    suburb: Optional[str] = None
    state_code: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    operating_hours: Optional[str] = None
    facilities: Optional[str] = None
    notes: Optional[str] = None
    contact_person: Optional[str] = None
    contact_title: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_mobile: Optional[str] = None
    contact_email: Optional[str] = None
    is_head_office: bool
    is_active: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None


class BranchStaffResponse(BaseModel):
    """Minimal user info for branch staff list."""
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    job_title: Optional[str] = None
    is_active: bool = True


class BranchProgramResponse(BaseModel):
    """Program info for branch program list."""
    model_config = ConfigDict(from_attributes=True)
    program_branch_id: int
    program_id: int
    program_name: str
    funding_type: Optional[str] = None
    is_active: bool = True
