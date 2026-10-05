"""Staff Profile schemas — profile, personal info, contact info, identification, preferences, emergency contacts."""
from datetime import date, datetime, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Staff Profile ─────────────────────────────────────────────────────────────

class StaffProfileCreate(BaseModel):
    staff_id: Optional[str] = Field(None, max_length=50)   # auto-generated if omitted
    user_id: Optional[str] = Field(None, max_length=50)    # linked AppUser.user_id
    first_name: str = Field(..., max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: str = Field(..., max_length=50)
    photo: Optional[str] = Field(None, max_length=255)
    work_email: Optional[str] = Field(None, max_length=255)
    status: str = Field("Active", max_length=30)


class StaffProfileUpdate(BaseModel):
    user_id: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    photo: Optional[str] = Field(None, max_length=255)
    work_email: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=30)


class StaffProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_id: str
    tenant_id: int
    user_id: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    photo: Optional[str] = None
    work_email: Optional[str] = None
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Personal Info ───────────────────────────────────────────────────────

class StaffPersonalInfoCreate(BaseModel):
    dob: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    nationality: Optional[str] = Field(None, max_length=50)
    language_spoken: Optional[str] = Field(None, max_length=100)
    permanent_street_no: Optional[str] = Field(None, max_length=50)
    permanent_area: Optional[str] = Field(None, max_length=50)
    permanent_city: Optional[str] = Field(None, max_length=50)
    permanent_state: Optional[str] = Field(None, max_length=50)
    permanent_post_code: Optional[str] = Field(None, max_length=10)
    permanent_country_id: Optional[int] = None
    same_as_permanent_address: Optional[bool] = None
    residential_street_no: Optional[str] = Field(None, max_length=50)
    residential_area: Optional[str] = Field(None, max_length=50)
    residential_city: Optional[str] = Field(None, max_length=50)
    residential_state: Optional[str] = Field(None, max_length=50)
    residential_post_code: Optional[str] = Field(None, max_length=10)
    residential_country_id: Optional[int] = None


class StaffPersonalInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personal_id: str
    staff_id: str
    tenant_id: int
    dob: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    nationality: Optional[str] = None
    language_spoken: Optional[str] = None
    permanent_street_no: Optional[str] = None
    permanent_area: Optional[str] = None
    permanent_city: Optional[str] = None
    permanent_state: Optional[str] = None
    permanent_post_code: Optional[str] = None
    permanent_country_id: Optional[int] = None
    same_as_permanent_address: Optional[bool] = None
    residential_street_no: Optional[str] = None
    residential_area: Optional[str] = None
    residential_city: Optional[str] = None
    residential_state: Optional[str] = None
    residential_post_code: Optional[str] = None
    residential_country_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Contact Info ────────────────────────────────────────────────────────

class StaffContactInfoCreate(BaseModel):
    primary_email: Optional[str] = Field(None, max_length=255)
    secondary_email: Optional[str] = Field(None, max_length=255)
    country_id: Optional[int] = None
    primary_contact_no: Optional[str] = Field(None, max_length=15)
    secondary_contact_no: Optional[str] = Field(None, max_length=15)


class StaffContactInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_contact_id: str
    staff_id: str
    tenant_id: str
    primary_email: Optional[str] = None
    secondary_email: Optional[str] = None
    country_id: Optional[int] = None
    primary_contact_no: Optional[str] = None
    secondary_contact_no: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Identification ──────────────────────────────────────────────────────

class StaffIdentificationCreate(BaseModel):
    identification_type: Optional[str] = Field(None, max_length=50)
    identification_number: Optional[str] = Field(None, max_length=50)
    document_attached: Optional[bool] = None
    expiry_date: Optional[date] = None
    verified: Optional[bool] = None
    verified_by: Optional[str] = Field(None, max_length=50)
    verified_date: Optional[date] = None


class StaffIdentificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_iden_id: str
    staff_id: str
    tenant_id: int
    identification_type: Optional[str] = None
    identification_number: Optional[str] = None
    document_attached: Optional[bool] = None
    expiry_date: Optional[date] = None
    verified: Optional[bool] = None
    verified_by: Optional[str] = None
    verified_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Preferences ────────────────────────────────────────────────────────

class StaffPreferencesCreate(BaseModel):
    preferred_shift_type: Optional[str] = Field(None, max_length=30)
    willing_weekend_work: Optional[bool] = None
    willing_public_holiday_work: Optional[bool] = None
    willing_sleepover_shift: Optional[bool] = None
    willing_active_overnight: Optional[bool] = None
    vehicle_available: Optional[bool] = None
    willing_to_travel: Optional[bool] = None
    travel_limit_enabled: Optional[bool] = None
    travel_radius_km: Optional[int] = None
    preferred_contact_time_from: Optional[time] = None
    preferred_contact_time_to: Optional[time] = None
    preferred_participant_gender: Optional[str] = Field(None, max_length=20)


class StaffPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_pref_id: str
    staff_id: str
    tenant_id: int
    preferred_shift_type: Optional[str] = None
    willing_weekend_work: Optional[bool] = None
    willing_public_holiday_work: Optional[bool] = None
    willing_sleepover_shift: Optional[bool] = None
    willing_active_overnight: Optional[bool] = None
    vehicle_available: Optional[bool] = None
    willing_to_travel: Optional[bool] = None
    travel_limit_enabled: Optional[bool] = None
    travel_radius_km: Optional[int] = None
    preferred_contact_time_from: Optional[time] = None
    preferred_contact_time_to: Optional[time] = None
    preferred_participant_gender: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Emergency Contact ───────────────────────────────────────────────────

class StaffEmergencyContactCreate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    relationship_with_staff: Optional[str] = Field(None, max_length=30)
    gender: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    street_no: Optional[str] = Field(None, max_length=50)
    area: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    post_code: Optional[str] = Field(None, max_length=50)
    country_id: Optional[int] = None
    primary_contact_no: Optional[str] = Field(None, max_length=15)
    secondary_contact_no: Optional[str] = Field(None, max_length=15)
    primary_email: Optional[str] = Field(None, max_length=255)
    secondary_email: Optional[str] = Field(None, max_length=255)
    is_primary_emerg_cntact: Optional[bool] = None


class StaffEmergencyContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    emergency_contact_id: str
    staff_id: str
    tenant_id: int
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    relationship_with_staff: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    street_no: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    post_code: Optional[str] = None
    country_id: Optional[int] = None
    primary_contact_no: Optional[str] = None
    secondary_contact_no: Optional[str] = None
    primary_email: Optional[str] = None
    secondary_email: Optional[str] = None
    is_primary_emerg_cntact: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
