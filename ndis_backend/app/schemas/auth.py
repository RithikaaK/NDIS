"""Authentication schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_code: Optional[str] = Field(None, description="Unique tenant slug code — optional when logging in by email alone")


class SendOtpRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)


class MeResponse(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    mobile: Optional[str] = None
    job_title: Optional[str] = None
    is_tenant_admin: bool
    last_login_at: Optional[datetime] = None


class MeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    mobile: Optional[str] = Field(None, max_length=20)
    job_title: Optional[str] = Field(None, max_length=150)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: int
    schema_name: str
    full_name: str
    is_tenant_admin: bool
    must_change_password: bool = False


class ForcedChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)
