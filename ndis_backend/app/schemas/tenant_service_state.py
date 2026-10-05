"""TenantServiceState schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TenantServiceStateCreate(BaseModel):
    state_code: str = Field(..., min_length=2, max_length=10, description="AU state code e.g. NSW, VIC")
    is_active: bool = True


class TenantServiceStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_state_id: int
    tenant_id: int
    state_code: str
    is_active: bool
    created_at: datetime
