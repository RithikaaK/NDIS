"""Staff Performance schemas — reviews, KPIs, and goals."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Performance Review ───────────────────────────────────────────────────────

class StaffPerformanceReviewCreate(BaseModel):
    review_period: Optional[str] = Field(None, max_length=20)
    review_type: Optional[str] = Field(None, max_length=30)
    review_date: Optional[date] = None
    reviewed_by: Optional[str] = Field(None, max_length=50)
    overall_score: Optional[Decimal] = None
    punctuality_score: Optional[Decimal] = None
    care_quality_score: Optional[Decimal] = None
    compliance_score: Optional[Decimal] = None
    communication_score: Optional[Decimal] = None
    teamwork_score: Optional[Decimal] = None
    reviewer_comments: Optional[str] = None
    staff_self_assessment: Optional[str] = None
    review_status: Optional[str] = Field(None, max_length=30)


class StaffPerformanceReviewUpdate(BaseModel):
    review_date: Optional[date] = None
    reviewed_by: Optional[str] = Field(None, max_length=50)
    overall_score: Optional[Decimal] = None
    punctuality_score: Optional[Decimal] = None
    care_quality_score: Optional[Decimal] = None
    compliance_score: Optional[Decimal] = None
    communication_score: Optional[Decimal] = None
    teamwork_score: Optional[Decimal] = None
    reviewer_comments: Optional[str] = None
    staff_self_assessment: Optional[str] = None
    review_status: Optional[str] = Field(None, max_length=30)


class StaffPerformanceReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    tenant_id: int
    staff_id: str
    review_period: Optional[str] = None
    review_type: Optional[str] = None
    review_date: Optional[date] = None
    reviewed_by: Optional[str] = None
    overall_score: Optional[Decimal] = None
    punctuality_score: Optional[Decimal] = None
    care_quality_score: Optional[Decimal] = None
    compliance_score: Optional[Decimal] = None
    communication_score: Optional[Decimal] = None
    teamwork_score: Optional[Decimal] = None
    reviewer_comments: Optional[str] = None
    staff_self_assessment: Optional[str] = None
    review_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── KPI ─────────────────────────────────────────────────────────────────────

class StaffKpiCreate(BaseModel):
    review_id: Optional[str] = Field(None, max_length=50)
    kpi_name: Optional[str] = Field(None, max_length=100)
    kpi_category: Optional[str] = Field(None, max_length=50)
    target_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    score: Optional[Decimal] = None
    weight_percent: Optional[Decimal] = None
    notes: Optional[str] = None
    period: Optional[str] = Field(None, max_length=20)


class StaffKpiUpdate(BaseModel):
    actual_value: Optional[Decimal] = None
    score: Optional[Decimal] = None
    notes: Optional[str] = None


class StaffKpiResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kpi_id: str
    tenant_id: int
    staff_id: str
    review_id: Optional[str] = None
    kpi_name: Optional[str] = None
    kpi_category: Optional[str] = None
    target_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    score: Optional[Decimal] = None
    weight_percent: Optional[Decimal] = None
    notes: Optional[str] = None
    period: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Goal ─────────────────────────────────────────────────────────────────────

class StaffGoalCreate(BaseModel):
    review_id: Optional[str] = Field(None, max_length=50)
    goal_title: Optional[str] = Field(None, max_length=200)
    goal_description: Optional[str] = None
    goal_category: Optional[str] = Field(None, max_length=50)
    goal_period: Optional[str] = Field(None, max_length=20)
    due_date: Optional[date] = None
    goal_status: Optional[str] = Field(None, max_length=30)
    set_by: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class StaffGoalUpdate(BaseModel):
    goal_status: Optional[str] = Field(None, max_length=30)
    completion_date: Optional[date] = None
    notes: Optional[str] = None
    due_date: Optional[date] = None


class StaffGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_id: str
    tenant_id: int
    staff_id: str
    review_id: Optional[str] = None
    goal_title: Optional[str] = None
    goal_description: Optional[str] = None
    goal_category: Optional[str] = None
    goal_period: Optional[str] = None
    due_date: Optional[date] = None
    goal_status: Optional[str] = None
    completion_date: Optional[date] = None
    set_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
