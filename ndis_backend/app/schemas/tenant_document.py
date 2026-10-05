"""TenantDocument schemas."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TenantDocumentCreate(BaseModel):
    document_category: str = Field(..., min_length=2, max_length=100,
                                    description="e.g. Registration, Insurance, Policy")
    document_name: str = Field(..., min_length=2, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=1000,
                           description="Storage path or URL of the uploaded file")
    file_size_kb: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    linked_to: Optional[str] = Field(None, max_length=255,
                                      description="What this document is linked to, e.g. 'NDIS Registration', 'Insurance'")
    expiry_date: Optional[date] = None


class TenantDocumentUpdate(BaseModel):
    document_category: Optional[str] = Field(None, min_length=2, max_length=100)
    document_name: Optional[str] = Field(None, min_length=2, max_length=255)
    linked_to: Optional[str] = Field(None, max_length=255)
    expiry_date: Optional[date] = None


class TenantDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    tenant_id: int
    document_category: str
    document_name: str
    file_path: str
    file_size_kb: Optional[int] = None
    mime_type: Optional[str] = None
    linked_to: Optional[str] = None
    expiry_date: Optional[date] = None
    uploaded_by: str
    uploaded_at: datetime
    is_deleted: bool
    deleted_at: Optional[datetime] = None
