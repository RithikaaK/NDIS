"""TenantRegistrationGroup schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TenantRegistrationGroupCreate(BaseModel):
    registration_group_code: str = Field(..., min_length=1, max_length=20)
    registration_group_name: str = Field(..., min_length=2, max_length=255)
    is_active: bool = True


class TenantRegistrationGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_reg_group_id: int
    tenant_id: int
    registration_group_code: str
    registration_group_name: str
    is_active: bool
    created_at: datetime
