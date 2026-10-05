"""Staff Shift schemas — features 4.3 Shift Scheduling, 4.4 Staff-to-Shift
Assignment, 4.5 Recurring Roster Management."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StaffShiftCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Mon .. 6=Sun")
    shift_type: Optional[str] = Field(None, max_length=50)
    start_hour: int = Field(..., ge=0, le=23)
    end_hour: int = Field(..., ge=1, le=24)
    location: Optional[str] = Field(None, max_length=200)
    shift_status: Optional[str] = Field("Confirmed", max_length=30)
    is_recurring: bool = False
    recurring_from: Optional[date] = None
    recurring_to: Optional[date] = None
    notes: Optional[str] = None


class StaffShiftUpdate(BaseModel):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    shift_type: Optional[str] = Field(None, max_length=50)
    start_hour: Optional[int] = Field(None, ge=0, le=23)
    end_hour: Optional[int] = Field(None, ge=1, le=24)
    location: Optional[str] = Field(None, max_length=200)
    shift_status: Optional[str] = Field(None, max_length=30)
    is_recurring: Optional[bool] = None
    recurring_from: Optional[date] = None
    recurring_to: Optional[date] = None
    notes: Optional[str] = None


class StaffShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shift_id: str
    tenant_id: int
    staff_id: str
    day_of_week: int
    shift_type: Optional[str] = None
    start_hour: int
    end_hour: int
    location: Optional[str] = None
    shift_status: Optional[str] = None
    is_recurring: bool
    recurring_from: Optional[date] = None
    recurring_to: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
