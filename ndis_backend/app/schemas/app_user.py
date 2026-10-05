"""AppUser schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AppUserCreate(BaseModel):
    branch_id: Optional[int] = None
    email: EmailStr
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    mobile: Optional[str] = Field(None, max_length=20)
    job_title: Optional[str] = Field(None, max_length=150)
    is_tenant_admin: bool = False
    is_active: bool = True
    role_ids: Optional[List[int]] = Field(default_factory=list)


class AppUserUpdate(BaseModel):
    branch_id: Optional[int] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    mobile: Optional[str] = Field(None, max_length=20)
    job_title: Optional[str] = Field(None, max_length=150)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role_ids: Optional[List[int]] = None


class AppUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    tenant_id: int
    branch_id: Optional[int] = None
    email: str
    first_name: str
    last_name: str
    mobile: Optional[str] = None
    job_title: Optional[str] = None
    # Populated by the list/get endpoints from the user_role table
    role_ids: List[int] = Field(default_factory=list)
    role_names: List[str] = Field(default_factory=list)
    is_tenant_admin: bool
    is_active: bool
    is_deleted: bool
    must_change_password: bool = False
    deleted_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
