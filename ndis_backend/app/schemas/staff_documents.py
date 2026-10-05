"""Staff Documents schemas — document repository."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class StaffDocumentResponse(BaseModel):
    """Response schema for a staff document record."""
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    staff_id: str
    tenant_id: int
    document_type: Optional[str] = None
    document_name: Optional[str] = None
    document_description: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_format: Optional[str] = None
    document_date: Optional[date] = None
    expiry_date: Optional[date] = None
    upload_date: Optional[date] = None
    document_status: Optional[str] = None
    expiry_alert_days: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
