"""Pydantic schemas for Staff Compliance Tracking (features 3.1–3.6)."""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ComplianceItemCreate(BaseModel):
    requirement_name:     str
    reference_no:         Optional[str]  = None
    category:             Optional[str]  = None
    requirement_type:     Optional[str]  = None
    completed_date:       Optional[date] = None
    expiry_date:          Optional[date] = None
    status:               Optional[str]  = "Pending"
    is_mandatory:         Optional[bool] = True
    reminder_days_before: Optional[str]  = "30"
    notes:                Optional[str]  = None


class ComplianceItemUpdate(BaseModel):
    requirement_name:     Optional[str]  = None
    reference_no:         Optional[str]  = None
    category:             Optional[str]  = None
    requirement_type:     Optional[str]  = None
    completed_date:       Optional[date] = None
    expiry_date:          Optional[date] = None
    status:               Optional[str]  = None
    is_mandatory:         Optional[bool] = None
    document_filename:    Optional[str]  = None
    document_url:         Optional[str]  = None
    reminder_days_before: Optional[str]  = None
    notes:                Optional[str]  = None


class ComplianceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    compliance_item_id:   str
    tenant_id:            str
    staff_id:             str
    requirement_name:     str
    reference_no:         Optional[str]      = None
    category:             Optional[str]      = None
    requirement_type:     Optional[str]      = None
    completed_date:       Optional[date]     = None
    expiry_date:          Optional[date]     = None
    status:               Optional[str]      = None
    is_mandatory:         Optional[bool]     = None
    document_filename:    Optional[str]      = None
    document_url:         Optional[str]      = None
    document_uploaded_at: Optional[datetime] = None
    reminder_days_before: Optional[str]      = None
    reminder_sent_at:     Optional[datetime] = None
    notes:                Optional[str]      = None
    created_at:           Optional[datetime] = None
    updated_at:           Optional[datetime] = None
    source:               Optional[str]      = "manual"


class ComplianceAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id:           str
    tenant_id:          str
    staff_id:           str
    compliance_item_id: str
    action_type:        Optional[str]      = None
    action_description: Optional[str]      = None
    previous_status:    Optional[str]      = None
    new_status:         Optional[str]      = None
    changed_by_name:    Optional[str]      = None
    notes:              Optional[str]      = None
    created_at:         Optional[datetime] = None
