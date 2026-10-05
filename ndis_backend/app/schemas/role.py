"""Role schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    role_code: str = Field(..., min_length=2, max_length=50)
    role_name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    is_active: bool = True


class RoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: int
    role_code: str
    role_name: str
    description: Optional[str] = None
    is_system_role: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
