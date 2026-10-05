"""Routers package — all API routers registered here."""
from app.routers.auth import router as auth_router
from app.routers.plans import router as plans_router
from app.routers.tenant_signup import router as tenant_signup_router
from app.routers.tenant_crud import router as tenant_crud_router
from app.routers.contacts import router as contacts_router
from app.routers.addresses import router as addresses_router
from app.routers.branches import router as branches_router
from app.routers.programs import router as programs_router
from app.routers.roles import router as roles_router
from app.routers.users import router as users_router
from app.routers.config import router as config_router
from app.routers.service_states import router as service_states_router
from app.routers.registration_groups import router as registration_groups_router
from app.routers.documents import router as documents_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.cross_branch_access import router as cross_branch_access_router

# Staff Management — split by domain
from app.routers.staff_profile import router as staff_profile_router
from app.routers.staff_employment import router as staff_employment_router
from app.routers.staff_compliance import router as staff_compliance_router
from app.routers.staff_availability import router as staff_availability_router
from app.routers.staff_shifts import router as staff_shifts_router
from app.routers.staff_timesheets import router as staff_timesheets_router
from app.routers.staff_leave import router as staff_leave_router
from app.routers.staff_documents import router as staff_documents_router
from app.routers.staff_performance import router as staff_performance_router
from app.routers.staff_compliance_tracking import router as staff_compliance_tracking_router

__all__ = [
    "auth_router",
    "plans_router",
    "tenant_signup_router",
    "tenant_crud_router",
    "contacts_router",
    "addresses_router",
    "branches_router",
    "programs_router",
    "roles_router",
    "users_router",
    "config_router",
    "service_states_router",
    "registration_groups_router",
    "documents_router",
    "audit_logs_router",
    "subscriptions_router",
    "cross_branch_access_router",
    # Staff
    "staff_profile_router",
    "staff_employment_router",
    "staff_compliance_router",
    "staff_availability_router",
    "staff_shifts_router",
    "staff_timesheets_router",
    "staff_leave_router",
    "staff_documents_router",
    "staff_performance_router",
    "staff_compliance_tracking_router",
]
