"""Branch ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Branch(Base):
    """Physical branch offices and service hubs.
    Lives in per-tenant schema (tenant_schema placeholder — resolved at request time).
    No tenant_id column: physical schema isolation guarantees tenant separation.
    """
    __tablename__ = "branch"
    __table_args__ = (
        UniqueConstraint("branch_code", name="UQ_branch_code"),
        {"schema": "tenant_schema"},
    )

    branch_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_code: Mapped[str] = mapped_column(String(50), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Location type (3.4)
    branch_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Hierarchy — parent branch (3.2)
    parent_branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Status enum (3.5): Active | Inactive | Temporarily Closed | Permanently Closed
    branch_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="Active")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    suburb: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    postcode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Location details (3.3)
    timezone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    operating_hours: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    facilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Contact person details
    contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_head_office: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )

    # Relationships — within tenant_schema only
    program_branches: Mapped[list["ProgramBranch"]] = relationship(
        "ProgramBranch", back_populates="branch", cascade="all, delete-orphan"
    )
    # Note: cross_branch_access uses logical branch_id refs (no FK) — not a relationship here.
    # Note: app_user.branch_id references this table (logical, no FK) — not a relationship here.
