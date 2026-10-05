"""Staff Leave schemas — leave types, requests, request dates, balances."""
from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ─── Leave Type (master catalogue) ───────────────────────────────────────────

class LeaveTypeCreate(BaseModel):
    leave_type_id: str = Field(..., max_length=50)
    leave_type_name: str = Field(..., max_length=50)
    leave_code: Optional[str] = Field(None, max_length=10)
    paid_leave: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=255)
    is_active: bool = True


class LeaveTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_type_id: str
    leave_type_name: str
    leave_code: Optional[str] = None
    paid_leave: Optional[bool] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


# ─── Staff Leave Request Date ─────────────────────────────────────────────────

class StaffLeaveRequestDateCreate(BaseModel):
    leave_date: Optional[date] = None
    leave_duration: Optional[str] = Field(None, max_length=20)
    leave_start_time: Optional[time] = None
    leave_end_time: Optional[time] = None
    leave_hours: Optional[Decimal] = None

    @field_validator("leave_date", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("leave_start_time", "leave_end_time", mode="before")
    @classmethod
    def empty_str_to_none_time(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("leave_hours", mode="before")
    @classmethod
    def empty_str_to_none_decimal(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class StaffLeaveRequestDateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_request_date_id: str
    leave_request_id: str
    tenant_id: int
    leave_date: Optional[date] = None
    leave_duration: Optional[str] = None
    leave_start_time: Optional[time] = None
    leave_end_time: Optional[time] = None
    leave_hours: Optional[Decimal] = None
    created_at: datetime


# ─── Staff Leave Request ──────────────────────────────────────────────────────

class StaffLeaveRequestCreate(BaseModel):
    leave_type_id: str = Field(..., max_length=50)
    reason_for_leave: Optional[str] = Field(None, max_length=100)
    supporting_document_uploaded: Optional[bool] = None
    submitted_date: Optional[date] = None
    submitted_time: Optional[time] = None
    backfill_required: Optional[bool] = None
    backfill_staff_id: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_days: Optional[int] = None
    dates: Optional[List[StaffLeaveRequestDateCreate]] = None

    @field_validator("start_date", "end_date", "submitted_date", mode="before")
    @classmethod
    def empty_str_to_none_sub_date(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("submitted_time", mode="before")
    @classmethod
    def empty_str_to_none_sub_time(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("reason_for_leave", "backfill_staff_id", mode="before")
    @classmethod
    def empty_str_to_none_str(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class StaffLeaveRequestUpdate(BaseModel):
    leave_status: Optional[str] = Field(None, max_length=30)
    approved_by: Optional[str] = Field(None, max_length=50)
    approval_date: Optional[date] = None
    decline_reason: Optional[str] = None
    participants_notified: Optional[bool] = None


class StaffLeaveRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_request_id: str
    staff_id: str
    tenant_id: int
    leave_type_id: str
    reason_for_leave: Optional[str] = None
    supporting_document_uploaded: Optional[bool] = None
    submitted_date: Optional[date] = None
    submitted_time: Optional[time] = None
    leave_status: Optional[str] = None
    approved_by: Optional[str] = None
    approval_date: Optional[date] = None
    decline_reason: Optional[str] = None
    backfill_required: Optional[bool] = None
    backfill_staff_id: Optional[str] = None
    participants_notified: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_days: Optional[int] = None
    dates: Optional[List[StaffLeaveRequestDateResponse]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Staff Leave Balance ──────────────────────────────────────────────────────

class StaffLeaveBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_balance_id: str
    staff_id: str
    tenant_id: int
    leave_type_id: str
    leave_period: Optional[str] = None
    opening_balance: Optional[Decimal] = None
    accrued_leave: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    remarks: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
