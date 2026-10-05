"""Roles and Permissions router — tenant-schema scoped."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import get_current_user
from app.database import get_tenant_session
from app.models import Permission, Role, RolePermission
from app.routers.helpers import log_audit, require_permission, verify_tenant_access
from app.schemas import MessageResponse, PermissionResponse, RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(tags=["Roles & Permissions"])

TTL_ROLES = 300
TTL_PERMISSIONS = 600

# ── Default NDIS roles & permission assignments ────────────────────────────────

_DEFAULT_ROLES = [
    ("SUPPORT_WORKER",     "Support Worker",     "Delivers direct support to NDIS participants in daily living activities."),
    ("TEAM_LEADER",        "Team Leader",        "Supervises support workers and coordinates day-to-day team operations."),
    ("COORDINATOR",        "Coordinator",        "Coordinates support plans and services for a caseload of participants."),
    ("BRANCH_MANAGER",     "Branch Manager",     "Oversees branch operations, staffing, compliance and service quality."),
    ("PROGRAM_MANAGER",    "Program Manager",    "Manages specific support programs including planning and reporting."),
    ("FINANCE_OFFICER",    "Finance Officer",    "Handles invoicing, claims, budgets, and financial reporting."),
    ("COMPLIANCE_OFFICER", "Compliance Officer", "Monitors regulatory compliance, incident reporting, and audits."),
    ("ROSTERING_OFFICER",  "Rostering Officer",  "Manages staff rosters, shift scheduling, and leave management."),
    ("HEALTH_SUPPORT",     "Health Support",     "Provides health-related support and monitors participant wellbeing."),
    ("ADMIN",              "Admin",              "Full system access. Manages users, roles, branches, programs, settings and all operational data."),
]

_ROLE_PERMS: dict = {
    "ADMIN": None,  # None = all permissions
    "BRANCH_MANAGER": [
        "branches:view","branches:edit",
        "programs:view","programs:create","programs:edit","programs:delete",
        "users:view","users:create","users:edit","users:role_assign",
        "roles:view","permissions:view",
        "participants:view","participants:create","participants:edit",
        "schedules:view","schedules:create","schedules:edit","schedules:delete",
        "progress_notes:view","progress_notes:create","progress_notes:edit",
        "incidents:view","incidents:create","incidents:edit",
        "documents:view","documents:create","documents:edit",
        "plans:view","plans:create","plans:edit",
        "reports:view","reports:create","reports:edit",
        "invoices:view","settings:view","audit:view",
    ],
    "PROGRAM_MANAGER": [
        "branches:view","programs:view","programs:create","programs:edit",
        "users:view","participants:view","participants:create","participants:edit",
        "schedules:view","schedules:create","schedules:edit",
        "progress_notes:view","progress_notes:create","progress_notes:edit",
        "incidents:view","incidents:create","incidents:edit",
        "documents:view","documents:create","documents:edit",
        "plans:view","plans:create","plans:edit",
        "reports:view","reports:create","invoices:view",
    ],
    "COORDINATOR": [
        "branches:view","programs:view","users:view",
        "participants:view","participants:create","participants:edit",
        "schedules:view","schedules:create","schedules:edit",
        "progress_notes:view","progress_notes:create","progress_notes:edit",
        "incidents:view","incidents:create",
        "documents:view","documents:create",
        "plans:view","plans:create","plans:edit",
        "reports:view","invoices:view",
    ],
    "TEAM_LEADER": [
        "branches:view","programs:view","users:view",
        "participants:view","participants:edit",
        "schedules:view","schedules:create","schedules:edit",
        "progress_notes:view","progress_notes:create","progress_notes:edit",
        "incidents:view","incidents:create",
        "documents:view","documents:create",
        "plans:view","reports:view",
    ],
    "SUPPORT_WORKER": [
        "participants:view","schedules:view",
        "progress_notes:view","progress_notes:create",
        "incidents:view","incidents:create",
        "documents:view","plans:view",
    ],
    "FINANCE_OFFICER": [
        "branches:view","programs:view","participants:view",
        "invoices:view","invoices:create","invoices:edit","invoices:delete",
        "reports:view","reports:create","reports:edit",
        "documents:view","documents:create","settings:view",
    ],
    "COMPLIANCE_OFFICER": [
        "branches:view","programs:view","users:view","participants:view",
        "incidents:view","incidents:create","incidents:edit",
        "documents:view","documents:create","documents:edit",
        "plans:view","reports:view","reports:create","reports:edit",
        "audit:view","settings:view",
    ],
    "ROSTERING_OFFICER": [
        "branches:view","programs:view","users:view","participants:view",
        "schedules:view","schedules:create","schedules:edit","schedules:delete",
        "documents:view","reports:view",
    ],
    "HEALTH_SUPPORT": [
        "participants:view","participants:edit","schedules:view",
        "progress_notes:view","progress_notes:create","progress_notes:edit",
        "incidents:view","incidents:create",
        "documents:view","documents:create",
        "plans:view","plans:edit",
    ],
}


async def _auto_seed_default_roles(db: AsyncSession) -> None:
    """Insert the standard NDIS roles (and their permission assignments) if the
    role table is empty.  Safe to call concurrently — duplicate-key errors are
    silently skipped.  The caller must commit afterwards."""
    import logging
    log = logging.getLogger(__name__)

    # Fetch all existing permissions once
    all_perms = (await db.scalars(select(Permission))).all()
    if not all_perms:
        log.warning("_auto_seed_default_roles: permission table is also empty — skipping seeding")
        return
    perm_map = {p.permission_code: p.permission_id for p in all_perms}
    all_perm_ids = list(perm_map.values())

    for role_code, role_name, description in _DEFAULT_ROLES:
        # Skip if already exists (any state)
        existing = await db.scalar(select(Role).where(Role.role_code == role_code))
        if existing:
            # Restore if soft-deleted
            if existing.is_deleted:
                existing.is_deleted = False
                existing.is_active = True
            role_id = existing.role_id
        else:
            new_role = Role(
                role_code=role_code,
                role_name=role_name,
                description=description,
                is_system_role=False,
                is_active=True,
                is_deleted=False,
            )
            db.add(new_role)
            await db.flush()
            role_id = new_role.role_id

        # Determine which permission IDs to assign
        target_perm_ids = all_perm_ids if _ROLE_PERMS.get(role_code) is None \
            else [perm_map[c] for c in _ROLE_PERMS.get(role_code, []) if c in perm_map]

        # Fetch already-assigned permissions for this role
        existing_rp = (await db.scalars(
            select(RolePermission).where(RolePermission.role_id == role_id)
        )).all()
        existing_pids = {rp.permission_id for rp in existing_rp}

        for pid in target_perm_ids:
            if pid not in existing_pids:
                db.add(RolePermission(role_id=role_id, permission_id=pid, granted=True))

    log.info("_auto_seed_default_roles: default roles seeded successfully")


@router.patch("/tenant/{tenant_id}/roles/{role_id}/activate", response_model=RoleResponse)
async def activate_role(
    tenant_id: int,
    role_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> RoleResponse:
    """Activate a deactivated role."""
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "roles:edit")
    role = await db.scalar(select(Role).where(Role.role_id == role_id, Role.is_deleted == False))  # noqa: E712
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    role.is_active = True
    await log_audit(db=db, user_id=current_user["user_id"], action="ACTIVATE_ROLE",
                    table_name="role", record_id=str(role_id), request=request)
    await db.commit()
    await db.refresh(role)
    await cache_delete(f"tenant:{tenant_id}:roles")
    return RoleResponse.model_validate(role)


@router.patch("/tenant/{tenant_id}/roles/{role_id}/deactivate", response_model=RoleResponse)
async def deactivate_role(
    tenant_id: int,
    role_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> RoleResponse:
    """Deactivate a role (users keep the assignment but the role is disabled)."""
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "roles:edit")
    role = await db.scalar(select(Role).where(Role.role_id == role_id, Role.is_deleted == False))  # noqa: E712
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System roles cannot be deactivated")
    role.is_active = False
    await log_audit(db=db, user_id=current_user["user_id"], action="DEACTIVATE_ROLE",
                    table_name="role", record_id=str(role_id), request=request)
    await db.commit()
    await db.refresh(role)
    await cache_delete(f"tenant:{tenant_id}:roles")
    return RoleResponse.model_validate(role)


@router.get("/tenant/{tenant_id}/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    tenant_id: int,
    role_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> RoleResponse:
    verify_tenant_access(tenant_id, current_user)
    role = await db.scalar(select(Role).where(Role.role_id == role_id, Role.is_deleted == False))  # noqa: E712
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return RoleResponse.model_validate(role)


@router.get("/tenant/{tenant_id}/roles/{role_id}/users")
async def list_role_users(
    tenant_id: int,
    role_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[Dict]:
    """List all users that have a given role assigned (active assignments only)."""
    from app.models import UserRole, AppUser
    from app.database import get_db_session
    verify_tenant_access(tenant_id, current_user)

    role = await db.scalar(select(Role).where(Role.role_id == role_id, Role.is_deleted == False))  # noqa
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # UserRole is in tenant schema; AppUser is in ndis_common — fetch UIDs first then look up users
    user_roles = (await db.scalars(
        select(UserRole).where(UserRole.role_id == role_id, UserRole.is_active == True)  # noqa
    )).all()
    user_ids = [ur.user_id for ur in user_roles]
    if not user_ids:
        return []

    # Fetch AppUser records from ndis_common
    from app.database import AsyncSessionLocal  # common DB
    from app.models import AppUser
    async with AsyncSessionLocal() as common_db:
        users = (await common_db.scalars(
            select(AppUser).where(
                AppUser.user_id.in_(user_ids),
                AppUser.tenant_id == tenant_id,
                AppUser.is_deleted == False,  # noqa
            )
        )).all()

    return [
        {
            "user_id": u.user_id, "first_name": u.first_name, "last_name": u.last_name,
            "email": u.email, "job_title": u.job_title, "branch_id": u.branch_id,
            "is_active": u.is_active,
        }
        for u in users
    ]


@router.delete("/tenant/{tenant_id}/roles/{role_id}", response_model=MessageResponse)
async def delete_role(
    tenant_id: int,
    role_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "roles:delete")

    role = await db.scalar(select(Role).where(Role.role_id == role_id, Role.is_deleted == False))  # noqa: E712
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System roles cannot be deleted",
        )

    from datetime import datetime, timezone
    role.is_deleted = True
    role.is_active = False
    role.deleted_at = datetime.now(timezone.utc)

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="SOFT_DELETE",
        table_name="role",
        record_id=str(role_id),
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:roles")
    return MessageResponse(message=f"Role '{role.role_name}' has been deactivated and deleted")


@router.get("/tenant/{tenant_id}/roles", response_model=List[RoleResponse])
async def list_roles(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[RoleResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:roles"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    # All roles in this schema belong to this tenant — no tenant_id filter needed
    roles = (await db.scalars(
        select(Role)
        .where(Role.is_active == True, Role.is_deleted == False)  # noqa: E712
        .order_by(Role.is_system_role.desc(), Role.role_id)
    )).all()

    # Auto-seed default NDIS roles the first time a tenant has none
    if not roles:
        await _auto_seed_default_roles(db)
        await db.commit()
        roles = (await db.scalars(
            select(Role)
            .where(Role.is_active == True, Role.is_deleted == False)  # noqa: E712
            .order_by(Role.role_id)
        )).all()

    result = [RoleResponse.model_validate(r).model_dump(mode="json") for r in roles]
    await cache_set(key, result, ttl=TTL_ROLES)
    return result


@router.post("/tenant/{tenant_id}/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    tenant_id: int,
    payload: RoleCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> RoleResponse:
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "roles:create")

    existing = await db.scalar(select(Role).where(
        Role.role_code == payload.role_code.strip().upper(),
    ))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with code '{payload.role_code}' already exists",
        )

    role = Role(
        role_code=payload.role_code.strip().upper(),
        role_name=payload.role_name.strip(),
        description=payload.description,
        is_system_role=False,
        is_active=payload.is_active,
    )
    db.add(role)
    await db.flush()

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="CREATE",
        table_name="role",
        record_id=str(role.role_id),
        new_values=payload.model_dump(),
        request=request,
    )
    await db.commit()
    await db.refresh(role)
    await cache_delete(f"tenant:{tenant_id}:roles")
    return RoleResponse.model_validate(role)


@router.put("/tenant/{tenant_id}/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    tenant_id: int,
    role_id: int,
    payload: RoleUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> RoleResponse:
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "roles:edit")

    role = await db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System roles cannot be modified by tenants",
        )

    old_values = {c.name: getattr(role, c.name) for c in role.__table__.columns}
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(role, field, val)

    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="UPDATE",
        table_name="role",
        record_id=str(role_id),
        old_values=old_values,
        new_values=update_data,
        request=request,
    )
    await db.commit()
    await db.refresh(role)
    await cache_delete(f"tenant:{tenant_id}:roles")
    return RoleResponse.model_validate(role)


@router.get("/tenant/{tenant_id}/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[PermissionResponse]:
    verify_tenant_access(tenant_id, current_user)

    key = f"tenant:{tenant_id}:permissions"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    permissions = (await db.scalars(
        select(Permission).order_by(Permission.module, Permission.permission_code)
    )).all()
    result = [PermissionResponse.model_validate(p).model_dump(mode="json") for p in permissions]
    await cache_set(key, result, ttl=TTL_PERMISSIONS)
    return result


@router.post(
    "/tenant/{tenant_id}/roles/{role_id}/permissions/{permission_id}",
    response_model=MessageResponse,
)
async def assign_permission_to_role(
    tenant_id: int,
    role_id: int,
    permission_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "permissions:assign")

    role = await db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify permissions on system roles",
        )

    perm = await db.scalar(select(Permission).where(Permission.permission_id == permission_id))
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    existing = await db.scalar(select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id,
    ))
    if existing:
        return MessageResponse(message="Permission is already assigned to this role")

    db.add(RolePermission(role_id=role_id, permission_id=permission_id, granted=True))
    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="GRANT_PERMISSION",
        table_name="role_permission",
        record_id=f"{role_id}:{permission_id}",
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:roles")
    return MessageResponse(
        message=f"Permission {perm.permission_code} assigned to role {role.role_name}"
    )


@router.get(
    "/tenant/{tenant_id}/roles/{role_id}/permissions",
    response_model=List[PermissionResponse],
)
async def list_role_permissions(
    tenant_id: int,
    role_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> List[PermissionResponse]:
    verify_tenant_access(tenant_id, current_user)

    role = await db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    key = f"tenant:{tenant_id}:roles:{role_id}:permissions"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    # Fetch all granted permissions for this role via join
    rps = (await db.scalars(
        select(RolePermission)
        .where(RolePermission.role_id == role_id, RolePermission.granted == True)  # noqa: E712
        .options(selectinload(RolePermission.permission))
    )).all()

    result = [
        PermissionResponse.model_validate(rp.permission).model_dump(mode="json")
        for rp in rps
        if rp.permission is not None
    ]
    await cache_set(key, result, ttl=TTL_PERMISSIONS)
    return result


@router.delete(
    "/tenant/{tenant_id}/roles/{role_id}/permissions/{permission_id}",
    response_model=MessageResponse,
)
async def revoke_permission_from_role(
    tenant_id: int,
    role_id: int,
    permission_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    verify_tenant_access(tenant_id, current_user)
    await require_permission(db, current_user, "permissions:assign")

    role = await db.scalar(select(Role).where(Role.role_id == role_id))
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify permissions on system roles",
        )

    perm = await db.scalar(select(Permission).where(Permission.permission_id == permission_id))
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    rp = await db.scalar(select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id,
    ))
    if not rp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission is not assigned to this role",
        )

    await db.delete(rp)
    await log_audit(
        db=db,
        user_id=current_user["user_id"],
        action="REVOKE_PERMISSION",
        table_name="role_permission",
        record_id=f"{role_id}:{permission_id}",
        old_values={"role_id": role_id, "permission_id": permission_id},
        request=request,
    )
    await db.commit()
    await cache_delete(f"tenant:{tenant_id}:roles")
    await cache_delete(f"tenant:{tenant_id}:roles:{role_id}:permissions")
    return MessageResponse(
        message=f"Permission {perm.permission_code} revoked from role {role.role_name}"
    )


# ── Sync default NDIS permissions into a tenant schema ───────────────────────
_DEFAULT_PERMISSIONS = [
    # branches
    ("branches:view",   "branches", "view",   "View branch details"),
    ("branches:create", "branches", "create", "Create a new branch"),
    ("branches:edit",   "branches", "edit",   "Update branch details"),
    ("branches:delete", "branches", "delete", "Soft-delete a branch"),
    # programs
    ("programs:view",   "programs", "view",   "View programs"),
    ("programs:create", "programs", "create", "Create programs"),
    ("programs:edit",   "programs", "edit",   "Edit programs"),
    ("programs:delete", "programs", "delete", "Delete programs"),
    # roles
    ("roles:view",   "roles", "view",   "View roles"),
    ("roles:create", "roles", "create", "Create roles"),
    ("roles:edit",   "roles", "edit",   "Edit roles"),
    ("roles:delete", "roles", "delete", "Delete roles"),
    # permissions
    ("permissions:view",   "permissions", "view",   "View permissions"),
    ("permissions:assign", "permissions", "assign", "Assign permissions to roles"),
    # users
    ("users:view",        "users", "view",        "View users"),
    ("users:create",      "users", "create",      "Create users"),
    ("users:edit",        "users", "edit",        "Edit user details"),
    ("users:delete",      "users", "delete",      "Deactivate users"),
    ("users:role_assign", "users", "role_assign", "Assign roles to users"),
    # settings
    ("settings:view", "settings", "view", "View tenant configuration"),
    ("settings:edit", "settings", "edit", "Edit tenant configuration"),
    # audit
    ("audit:view", "audit", "view", "View audit logs"),
    # participants
    ("participants:view",   "participants", "view",   "View participants"),
    ("participants:create", "participants", "create", "Create participants"),
    ("participants:edit",   "participants", "edit",   "Edit participants"),
    ("participants:delete", "participants", "delete", "Delete participants"),
    # schedules
    ("schedules:view",   "schedules", "view",   "View shifts and schedules"),
    ("schedules:create", "schedules", "create", "Create shifts and schedules"),
    ("schedules:edit",   "schedules", "edit",   "Edit shifts and schedules"),
    ("schedules:delete", "schedules", "delete", "Delete shifts and schedules"),
    # progress notes
    ("progress_notes:view",   "progress_notes", "view",   "View progress notes"),
    ("progress_notes:create", "progress_notes", "create", "Create progress notes"),
    ("progress_notes:edit",   "progress_notes", "edit",   "Edit progress notes"),
    ("progress_notes:delete", "progress_notes", "delete", "Delete progress notes"),
    # incidents
    ("incidents:view",   "incidents", "view",   "View incidents"),
    ("incidents:create", "incidents", "create", "Create incidents"),
    ("incidents:edit",   "incidents", "edit",   "Edit incidents"),
    ("incidents:delete", "incidents", "delete", "Delete incidents"),
    # documents
    ("documents:view",   "documents", "view",   "View documents"),
    ("documents:create", "documents", "create", "Upload documents"),
    ("documents:edit",   "documents", "edit",   "Edit documents"),
    ("documents:delete", "documents", "delete", "Delete documents"),
    # plans
    ("plans:view",   "plans", "view",   "View support plans"),
    ("plans:create", "plans", "create", "Create support plans"),
    ("plans:edit",   "plans", "edit",   "Edit support plans"),
    ("plans:delete", "plans", "delete", "Delete support plans"),
    # reports
    ("reports:view",   "reports", "view",   "View reports"),
    ("reports:create", "reports", "create", "Create reports"),
    ("reports:edit",   "reports", "edit",   "Edit reports"),
    # invoices
    ("invoices:view",   "invoices", "view",   "View invoices"),
    ("invoices:create", "invoices", "create", "Create invoices"),
    ("invoices:edit",   "invoices", "edit",   "Edit invoices"),
    ("invoices:delete", "invoices", "delete", "Delete invoices"),
]


@router.post(
    "/tenant/{tenant_id}/permissions/sync",
    response_model=MessageResponse,
)
async def sync_default_permissions(
    tenant_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    """Insert any missing default NDIS permissions into the tenant schema.

    Idempotent — existing permissions are untouched.
    Requires tenant admin or IT_SUPPORT role.
    """
    verify_tenant_access(tenant_id, current_user)
    if not current_user.get("is_tenant_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can sync permissions",
        )

    existing = (await db.scalars(select(Permission))).all()
    existing_codes = {p.permission_code for p in existing}

    inserted = 0
    for perm_code, module, action, description in _DEFAULT_PERMISSIONS:
        if perm_code not in existing_codes:
            db.add(Permission(
                permission_code=perm_code,
                module=module,
                action=action,
                description=description,
                is_active=True,
            ))
            inserted += 1

    if inserted:
        await db.commit()
        await cache_delete(f"tenant:{tenant_id}:permissions")

    return MessageResponse(
        message=f"Permissions synced: {inserted} inserted, {len(existing_codes)} already existed"
    )
