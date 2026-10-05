"""Tenant signup, update, and response schemas."""
import re
from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class TenantSignupBase(BaseModel):
    """Base fields required for tenant registration."""
    organisation_name: str = Field(..., min_length=2, max_length=255)
    trading_name: Optional[str] = Field(None, max_length=255)
    abn: str = Field(..., description="Australian Business Number (11 digits)")
    acn: Optional[str] = Field(None, max_length=9)
    organisation_type: Optional[str] = Field(None, max_length=50)
    primary_email: EmailStr
    primary_phone: Optional[str] = Field(None, max_length=20)
    website_url: Optional[str] = Field(None, max_length=500)
    timezone: str = Field("Australia/Sydney", max_length=100)
    plan_id: Optional[int] = Field(None, description="Optional subscription plan ID")

    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, max_length=64)
    admin_mobile: Optional[str] = Field(None, max_length=20)
    admin_job_title: Optional[str] = Field("Chief Executive Officer", max_length=150)

    head_office_address_line1: Optional[str] = Field(None, max_length=255)
    head_office_suburb: Optional[str] = Field(None, max_length=100)
    head_office_state_code: Optional[str] = Field("NSW", max_length=10)
    head_office_postcode: Optional[str] = Field(None, max_length=10)

    @field_validator("abn", mode="before")
    @classmethod
    def validate_abn(cls, v: Any) -> str:
        if not v:
            raise ValueError("ABN is required")
        digits = re.sub(r"\D", "", str(v))
        if len(digits) != 11:
            raise ValueError("ABN must contain exactly 11 digits")
        return digits

    @field_validator("acn", mode="before")
    @classmethod
    def validate_acn(cls, v: Any) -> Optional[str]:
        if not v:
            return None
        digits = re.sub(r"\D", "", str(v))
        if len(digits) != 9:
            raise ValueError("ACN must contain exactly 9 digits")
        return digits


class TenantSignupRegistered(TenantSignupBase):
    """Signup payload for Registered NDIS Providers."""
    ndis_registration_number: str = Field(..., min_length=3, max_length=20)
    registration_expiry_date: Optional[date] = None
    provider_type: str = "Registered"

    @field_validator("ndis_registration_number", mode="before")
    @classmethod
    def validate_ndis_number(cls, v: Any) -> str:
        if not v:
            raise ValueError("NDIS Registration Number is required")
        val = str(v).strip()
        # Allow letters, digits, hyphens only
        if not re.match(r'^[A-Za-z0-9\-]+$', val):
            raise ValueError(
                "NDIS Registration Number may only contain letters, numbers and hyphens"
            )
        # Must contain at least one digit — pure alphabets not accepted
        if not re.search(r'[0-9]', val):
            raise ValueError(
                "NDIS Registration Number must contain at least one number (e.g. 4-050-0123)"
            )
        return val


class TenantSignupNonRegistered(TenantSignupBase):
    """Signup payload for Non-Registered NDIS Providers.
    ABN is optional — providers who skip org details during signup won't have one yet.
    """
    # Override base: ABN is optional for non-registered providers
    abn: Optional[str] = Field(None, description="ABN (optional for non-registered providers)")
    # NULL when user skips setup; "Non-Registered" when user explicitly selects it
    provider_type: Optional[str] = Field(None, description="NDIS registration status — null if user skipped setup")

    @field_validator("abn", mode="before")
    @classmethod
    def validate_abn(cls, v: Any) -> Optional[str]:   # type: ignore[override]
        if not v:
            return None
        digits = re.sub(r"\D", "", str(v))
        if len(digits) != 11:
            raise ValueError("ABN must contain exactly 11 digits")
        return digits


class TenantUpdate(BaseModel):
    """Payload to update an existing tenant's profile."""
    organisation_name: Optional[str] = Field(None, min_length=2, max_length=255)
    trading_name: Optional[str] = Field(None, max_length=255)
    abn: Optional[str] = Field(None, max_length=11)
    acn: Optional[str] = Field(None, max_length=9)
    ndis_registration_number: Optional[str] = Field(None, max_length=20)
    registration_expiry_date: Optional[date] = None
    organisation_type: Optional[str] = Field(None, max_length=50)
    provider_type: Optional[str] = Field(None, description="NDIS registration status: 'Registered', 'Non-Registered', or null")
    primary_email: Optional[EmailStr] = None
    primary_phone: Optional[str] = Field(None, max_length=20)
    website_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)

    @field_validator("provider_type", mode="before")
    @classmethod
    def validate_provider_type(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if v not in ("Registered", "Non-Registered"):
            raise ValueError("provider_type must be 'Registered', 'Non-Registered', or null")
        return v


class TenantResponse(BaseModel):
    """Response schema for tenant organisation details."""
    model_config = ConfigDict(from_attributes=True)

    tenant_id: int
    tenant_code: Optional[str] = None
    organisation_name: str
    trading_name: Optional[str] = None
    abn: Optional[str] = None
    acn: Optional[str] = None
    is_registered_provider: bool
    ndis_registration_number: Optional[str] = None
    registration_expiry_date: Optional[date] = None
    provider_type: Optional[str] = None
    organisation_type: Optional[str] = None
    primary_email: str
    primary_phone: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    timezone: str
    status: str
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None


class TenantListResponse(BaseModel):
    """Paginated list of tenant records."""
    total: int
    skip: int
    limit: int
    items: List[TenantResponse]


class DomainCheckResponse(BaseModel):
    """Response for the domain availability check endpoint."""
    available: bool
    domain: str
    message: str
