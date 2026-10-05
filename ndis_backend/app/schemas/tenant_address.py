"""Tenant address schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TenantAddressCreate(BaseModel):
    address_type: str = Field(..., max_length=50)
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    suburb: str = Field(..., max_length=100)
    state_code: str = Field(..., max_length=10)
    postcode: str = Field(..., max_length=10)
    country_code: str = Field("AUS", max_length=3)
    is_primary: bool = False


class TenantAddressUpdate(BaseModel):
    address_type: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    suburb: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, max_length=10)
    postcode: Optional[str] = Field(None, max_length=10)
    country_code: Optional[str] = Field(None, max_length=3)
    is_primary: Optional[bool] = None


class TenantAddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    address_id: int
    tenant_id: int
    address_type: str
    address_line1: str
    address_line2: Optional[str] = None
    suburb: str
    state_code: str
    postcode: str
    country_code: str
    is_primary: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
