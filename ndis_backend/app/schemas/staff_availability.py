"""Staff Availability schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StaffAvailabilityCreate(BaseModel):
    availability_type: Optional[str] = Field(None, max_length=30)
    availability_effective_from: Optional[datetime] = None
    availability_effective_to: Optional[datetime] = None
    availability_status: Optional[str] = Field(None, max_length=30)
    current_shift_id: Optional[str] = Field(None, max_length=50)
    available_for_overtime: Optional[bool] = None
    available_for_on_call: Optional[bool] = None
    availability_notes: Optional[str] = None
    is_active: bool = True


class StaffAvailabilityUpdate(BaseModel):
    availability_type: Optional[str] = Field(None, max_length=30)
    availability_effective_from: Optional[datetime] = None
    availability_effective_to: Optional[datetime] = None
    availability_status: Optional[str] = Field(None, max_length=30)
    available_for_overtime: Optional[bool] = None
    available_for_on_call: Optional[bool] = None
    availability_notes: Optional[str] = None
    is_active: Optional[bool] = None


class StaffAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    availability_id: str
    staff_id: str
    tenant_id: int
    availability_type: Optional[str] = None
    availability_effective_from: Optional[datetime] = None
    availability_effective_to: Optional[datetime] = None
    availability_status: Optional[str] = None
    current_shift_id: Optional[str] = None
    available_for_overtime: Optional[bool] = None
    available_for_on_call: Optional[bool] = None
    availability_notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
