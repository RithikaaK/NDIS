"""Staff Timesheets schemas — timesheet headers and lines."""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Staff Timesheet Header ───────────────────────────────────────────────────

class StaffTimesheetHeaderCreate(BaseModel):
    work_date: Optional[date] = None
    timesheet_status: Optional[str] = Field("Draft", max_length=30)
    notes: Optional[str] = None


class StaffTimesheetHeaderUpdate(BaseModel):
    timesheet_status: Optional[str] = Field(None, max_length=30)
    approved_by: Optional[str] = Field(None, max_length=50)
    approval_date: Optional[date] = None
    rejection_reason: Optional[str] = Field(None, max_length=100)
    total_overtime_hours: Optional[Decimal] = None
    notes: Optional[str] = None


class StaffTimesheetHeaderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timesheet_id: str
    staff_id: str
    tenant_id: int
    work_date: Optional[date] = None
    timesheet_status: Optional[str] = None
    submitted_date: Optional[date] = None
    approval_date: Optional[date] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    total_overtime_hours: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Timesheet Line ─────────────────────────────────────────────────────

class StaffTimesheetLineCreate(BaseModel):
    shift_id: Optional[str] = Field(None, max_length=20)
    ndis_no: Optional[str] = Field(None, max_length=50)
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    actual_clock_on_time: Optional[time] = None
    actual_clock_off_time: Optional[time] = None
    break_taken: Optional[bool] = None
    break_duration_minutes: Optional[int] = None
    care_note_submitted: Optional[bool] = None
    line_status: Optional[str] = Field("Pending", max_length=30)


class StaffTimesheetLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timesheet_line_id: str
    timesheet_id: str
    tenant_id: int
    shift_id: Optional[str] = None
    ndis_no: Optional[str] = None
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    actual_clock_on_time: Optional[time] = None
    actual_clock_off_time: Optional[time] = None
    break_taken: Optional[bool] = None
    break_duration_minutes: Optional[int] = None
    care_note_submitted: Optional[bool] = None
    line_status: Optional[str] = None
    created_at: datetime
