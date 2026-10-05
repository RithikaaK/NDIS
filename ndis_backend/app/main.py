"""FastAPI Main Application Entry Point for NDIS Management System - Tenant Module."""
import logging
import os
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.exceptions import FieldValidationError
from app.core.startup import provision_platform, seed_subscription_plans, seed_leave_types, migrate_tenant_document_linked_to, migrate_branch_columns, migrate_cross_branch_access_table, migrate_tenant_config_columns, migrate_staff_tables, migrate_staff_permissions, migrate_admin_roles, migrate_staff_personal_info_columns, migrate_staff_profile_user_id, migrate_timesheet_line_columns
from app.routers import (
    auth_router,
    plans_router,
    tenant_signup_router,
    tenant_crud_router,
    contacts_router,
    addresses_router,
    branches_router,
    programs_router,
    roles_router,
    users_router,
    config_router,
    service_states_router,
    registration_groups_router,
    documents_router,
    audit_logs_router,
    subscriptions_router,
    cross_branch_access_router,
    # Staff Management — split by domain
    staff_profile_router,
    staff_employment_router,
    staff_compliance_router,
    staff_availability_router,
    staff_shifts_router,
    staff_timesheets_router,
    staff_leave_router,
    staff_documents_router,
    staff_performance_router,
    staff_compliance_tracking_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — runs startup tasks before accepting requests."""
    await provision_platform()                     # 1. create ndis_common schema + tables (fresh DB)
    await seed_subscription_plans()               # 2. seed subscription plans if empty
    await seed_leave_types()                      # 2a. seed standard leave types if empty
    await migrate_tenant_document_linked_to()     # 3. add linked_to col to tenant_document (idempotent)
    await migrate_branch_columns()                # 4. add branch type/status/hierarchy cols (idempotent)
    await migrate_cross_branch_access_table()     # 5. create/rebuild cross_branch_access table (idempotent)
    await migrate_tenant_config_columns()         # 6. add new config cols for 8.1–8.7 (idempotent)
    await migrate_staff_tables()                  # 7. create staff management tables in existing tenants (idempotent)
    await migrate_staff_personal_info_columns()   # 7a. add nationality/language_spoken to staff_personal_info (idempotent)
    await migrate_staff_permissions()             # 8. seed staff permission codes + role assignments (idempotent)
    await migrate_admin_roles()                   # 9. ensure is_tenant_admin users have ADMIN role (idempotent)
    await migrate_staff_profile_user_id()         # 10. add user_id col + backfill StaffProfiles for existing users (idempotent)
    await migrate_timesheet_line_columns()        # 11. widen staff_timesheet_line.timesheet_id/shift_id to NVARCHAR(50) (idempotent)
    yield
    # (add shutdown tasks here if needed)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready FastAPI backend for the Australian NDIS Management System SaaS - Tenant Module",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers under /api/v1
PREFIX = settings.API_V1_STR

app.include_router(auth_router,          prefix=PREFIX)
app.include_router(plans_router,         prefix=PREFIX)
app.include_router(tenant_signup_router, prefix=PREFIX)
app.include_router(tenant_crud_router,   prefix=PREFIX)
app.include_router(contacts_router,      prefix=PREFIX)
app.include_router(addresses_router,     prefix=PREFIX)
app.include_router(branches_router,      prefix=PREFIX)
app.include_router(programs_router,      prefix=PREFIX)
app.include_router(roles_router,         prefix=PREFIX)
app.include_router(users_router,         prefix=PREFIX)
app.include_router(config_router,              prefix=PREFIX)
app.include_router(service_states_router,      prefix=PREFIX)
app.include_router(registration_groups_router, prefix=PREFIX)
app.include_router(documents_router,           prefix=PREFIX)
app.include_router(audit_logs_router,          prefix=PREFIX)
app.include_router(subscriptions_router,          prefix=PREFIX)
app.include_router(cross_branch_access_router,    prefix=PREFIX)
# Staff Management
app.include_router(staff_profile_router,          prefix=PREFIX)
app.include_router(staff_employment_router,       prefix=PREFIX)
app.include_router(staff_compliance_router,       prefix=PREFIX)
app.include_router(staff_availability_router,     prefix=PREFIX)
app.include_router(staff_shifts_router,           prefix=PREFIX)
app.include_router(staff_timesheets_router,       prefix=PREFIX)
app.include_router(staff_leave_router,            prefix=PREFIX)
app.include_router(staff_documents_router,        prefix=PREFIX)
app.include_router(staff_performance_router,             prefix=PREFIX)
app.include_router(staff_compliance_tracking_router,     prefix=PREFIX)

# Serve uploaded compliance documents as static files
_uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


@app.exception_handler(FieldValidationError)
async def field_validation_error_handler(request: Request, exc: FieldValidationError):
    """Converts a field-tagged business-rule error into the unified field_errors shape."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "field_errors": {exc.field: exc.message},
        },
    )


def _field_name_from_loc(loc) -> str | None:
    """Pulls the actual field name out of a pydantic/FastAPI error `loc` tuple,
    e.g. ('body', 'abn') -> 'abn', ('body', 'dates', 0, 'leave_date') -> 'leave_date'."""
    for part in reversed(loc):
        if isinstance(part, str) and part not in ("body", "query", "path", "header", "cookie"):
            return part
    return None


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """Reshapes FastAPI/pydantic 422 validation errors into the same
    {"detail": ..., "field_errors": {...}} shape used by FieldValidationError,
    so the frontend only needs one parsing path for both. `detail` keeps
    FastAPI's original array-of-errors format for backward compatibility
    with any existing code that already reads it."""
    field_errors: dict[str, str] = {}
    for err in exc.errors():
        field = _field_name_from_loc(err.get("loc", ()))
        if not field:
            continue
        msg = err.get("msg", "Invalid value")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        field_errors[field] = msg
    return JSONResponse(
        status_code=422,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "field_errors": field_errors,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Global fallback — logs full traceback and returns a structured 500 JSON body."""
    tb = traceback.format_exc()
    logger.error(
        "Unhandled exception on %s %s\n%s",
        request.method, request.url.path, tb,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"{type(exc).__name__}: {exc}",
            "path": str(request.url.path),
        },
    )


@app.get("/", tags=["Health Check"])
def health_check():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "module": "Tenant Management Module",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_engine": "Microsoft SQL Server (aioodbc)",
        "docs_url": "/docs",
    }
