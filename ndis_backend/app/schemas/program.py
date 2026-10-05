"""Program schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProgramCreate(BaseModel):
    program_code: str = Field(..., min_length=2, max_length=50)
    program_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    funding_type: Optional[str] = Field("NDIS", max_length=50)
    is_active: bool = True
    branch_ids: Optional[List[int]] = Field(default_factory=list)


class ProgramUpdate(BaseModel):
    program_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    funding_type: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    program_id: int
    program_code: str
    program_name: str
    description: Optional[str] = None
    funding_type: Optional[str] = None
    is_active: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    branch_ids: List[int] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _extract_branch_ids(cls, v):
        """When validating from an ORM Program object, extract branch_ids from
        the program_branches relationship if it has been eagerly loaded."""
        if hasattr(v, "__table__"):  # SQLAlchemy ORM object
            data: dict = {col.name: getattr(v, col.name) for col in v.__table__.columns}
            # If the relationship was loaded via selectinload, it lives in __dict__
            pbs = v.__dict__.get("program_branches") or []
            data["branch_ids"] = [pb.branch_id for pb in pbs]
            return data
        return v
