"""Program ORM model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Program(Base):
    """Service lines and programs offered by the tenant.
    Lives in per-tenant schema (tenant_schema placeholder — resolved at request time).
    No tenant_id column: physical schema isolation guarantees tenant separation.
    """
    __tablename__ = "program"
    __table_args__ = (
        UniqueConstraint("program_code", name="UQ_program_code"),
        {"schema": "tenant_schema"},
    )

    program_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_code: Mapped[str] = mapped_column(String(50), nullable=False)
    program_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    funding_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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
        "ProgramBranch", back_populates="program", cascade="all, delete-orphan"
    )
