"""CrossBranchAccess ORM model — full request/approval/temporary/emergency schema (4.1–4.7)."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CrossBranchAccess(Base):
    """Cross-branch access records — planned requests, temporary grants, and emergency access.

    Lives in per-tenant schema.  All user_id references are logical (string) because
    app_user lives in ndis_common and cross-schema FKs are not enforced.
    Both home_branch_id and target_branch_id are logical integers — no DB FK so that a
    deleted branch doesn't break historical records.

    Status lifecycle:
        pending  → approved → active → expired / revoked
        pending  → rejected
        (emergency) → active (requires_review=True) → reviewed
    """
    __tablename__ = "cross_branch_access"
    __table_args__ = {"schema": "tenant_schema"}

    access_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Who ───────────────────────────────────────────────────────────────────
    staff_user_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    home_branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_branch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # ── What is being accessed ────────────────────────────────────────────────
    # 4.6: restrict to a specific participant (NULL = all participants in branch)
    participant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    participant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # JSON list of permitted activities e.g. '["Support Worker","Plan Management"]'
    permitted_activities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Why ───────────────────────────────────────────────────────────────────
    access_reason: Mapped[str] = mapped_column(String(500), nullable=False)
    services_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── When (4.4 temporary access) ───────────────────────────────────────────
    access_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    access_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Access type ───────────────────────────────────────────────────────────
    # access_type: 'planned' | 'emergency'
    access_type: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    emergency_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # True for emergency access granted immediately (bypass approval) — flags for later review
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Status ────────────────────────────────────────────────────────────────
    # pending | approved | rejected | active | expired | revoked
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    # ── Request (4.2) ─────────────────────────────────────────────────────────
    requested_by: Mapped[str] = mapped_column(String(50), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )

    # ── Approval / Rejection (4.3) ────────────────────────────────────────────
    approved_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_comments: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Revocation ────────────────────────────────────────────────────────────
    revoked_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoke_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Standard ─────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.sysdatetimeoffset(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.sysdatetimeoffset(), nullable=True
    )
