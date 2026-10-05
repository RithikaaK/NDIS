"""Permission schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    permission_id: int
    permission_code: str
    module: str
    action: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
