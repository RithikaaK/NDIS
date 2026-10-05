"""Pydantic schemas for Cross-Branch Access (4.1–4.7)."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

ACCESS_STATUSES = ["pending", "approved", "rejected", "active", "expired", "revoked"]
ACCESS_TYPES    = ["planned", "emergency"]


class CrossBranchAccessRequest(BaseModel):
    """4.2 — Staff submits a planned access request."""
    staff_user_id: str
    home_branch_id: int
    target_branch_id: int
    access_reason: str
    services_description: Optional[str] = None
    access_start: Optional[datetime] = None
    access_end: Optional[datetime] = None
    # 4.6 participant-level access
    participant_id: Optional[str] = None
    participant_name: Optional[str] = None
    permitted_activities: Optional[str] = None  # JSON string

    @field_validator("access_reason")
    @classmethod
    def reason_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("access_reason is required")
        return v.strip()


class EmergencyAccessRequest(BaseModel):
    """4.5 — Emergency access granted immediately, flagged for review."""
    staff_user_id: str
    home_branch_id: int
    target_branch_id: int
    emergency_reason: str
    services_description: Optional[str] = None
    access_start: Optional[datetime] = None
    access_end: Optional[datetime] = None
    participant_id: Optional[str] = None
    participant_name: Optional[str] = None
    permitted_activities: Optional[str] = None

    @field_validator("emergency_reason")
    @classmethod
    def reason_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("emergency_reason is required")
        return v.strip()


class ApproveRequest(BaseModel):
    """4.3 — Admin approves an access request."""
    approval_comments: Optional[str] = None
    # Optionally override the period on approval
    access_start: Optional[datetime] = None
    access_end: Optional[datetime] = None
    permitted_activities: Optional[str] = None


class RejectRequest(BaseModel):
    """4.3 — Admin rejects an access request."""
    rejection_reason: Optional[str] = None


class RevokeRequest(BaseModel):
    """Revoke an active access grant."""
    revoke_reason: Optional[str] = None


class ReviewRequest(BaseModel):
    """Mark an emergency access record as reviewed."""
    review_notes: Optional[str] = None


class CrossBranchAccessResponse(BaseModel):
    access_id: int
    staff_user_id: str
    home_branch_id: int
    target_branch_id: int
    participant_id: Optional[str] = None
    participant_name: Optional[str] = None
    permitted_activities: Optional[str] = None
    access_reason: str
    services_description: Optional[str] = None
    access_start: Optional[datetime] = None
    access_end: Optional[datetime] = None
    access_type: str
    is_emergency: bool
    emergency_reason: Optional[str] = None
    requires_review: bool
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    status: str
    requested_by: str
    requested_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_comments: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    revoked_by: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
