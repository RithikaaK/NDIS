"""Tenant contact schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantContactCreate(BaseModel):
    contact_type: str = Field(..., max_length=50)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    position_title: Optional[str] = Field(None, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    is_active: bool = True


class TenantContactUpdate(BaseModel):
    contact_type: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    position_title: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class TenantContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contact_id: int
    tenant_id: int
    contact_type: str
    first_name: str
    last_name: str
    position_title: Optional[str] = None
    email: str
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
