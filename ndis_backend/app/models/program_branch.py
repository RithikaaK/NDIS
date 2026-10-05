"""ProgramBranch ORM model."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProgramBranch(Base):
    """Branch mapping linking which programs are active at specific branches.
    Lives in per-tenant schema (tenant_schema placeholder — resolved at request time).
    """
    __tablename__ = "program_branch"
    __table_args__ = (
        UniqueConstraint("program_id", "branch_id", name="UQ_program_branch_program_branch"),
        {"schema": "tenant_schema"},
    )

    program_branch_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_schema.program.program_id"), nullable=False
    )
    branch_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_schema.branch.branch_id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )

    # Relationships
    program: Mapped["Program"] = relationship("Program", back_populates="program_branches")
    branch: Mapped["Branch"] = relationship("Branch", back_populates="program_branches")
