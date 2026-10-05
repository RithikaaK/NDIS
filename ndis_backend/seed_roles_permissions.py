#!/usr/bin/env python3
"""
seed_roles_permissions.py
─────────────────────────
Populates an existing tenant's database with:
  • All NDIS permissions (in module:action format, via the sync endpoint)
  • 10 standard NDIS roles
  • Role → permission assignments

Run this against a tenant created BEFORE the new permission codes were
added to tenant_schema.py, or any time to ensure roles and permissions
are in sync.

Prerequisites:
  pip install requests  (or: pip install requests --break-system-packages)
  Backend must be running: uvicorn app.main:app --reload

Usage:
  cd C:\\new\\ndis_backend
  python seed_roles_permissions.py
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────────────────────
BASE_URL       = "http://localhost:8000/api/v1"
ADMIN_EMAIL    = os.getenv("SEED_ADMIN_EMAIL",    "john.smith@sunshine-ndis.com.au")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@1234")
TENANT_CODE    = os.getenv("SEED_TENANT_CODE",    "SUNSHI-001")

SEP  = "═" * 60
SEP2 = "─" * 60

HEADERS: dict = {}


def ok(msg):   print(f"   ✓  {msg}")
def info(msg): print(f"   →  {msg}")
def warn(msg): print(f"   ⚠  {msg}")
def fail(msg): print(f"   ✗  {msg}"); sys.exit(1)


def api_post(path, body=None):
    r = requests.post(f"{BASE_URL}{path}", json=body or {}, headers=HEADERS)
    try:    return r.status_code, r.json()
    except: return r.status_code, {"detail": r.text}


def api_get(path):
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS)
    try:
        data = r.json()
        return r.status_code, data if isinstance(data, list) else data
    except:
        return r.status_code, []


# ── 10 Standard NDIS roles ────────────────────────────────────────────────────
ROLES = [
    {"role_code": "SUPPORT_WORKER",
     "role_name": "Support Worker",
     "description": "Provides direct support to NDIS participants in daily living activities, personal care, and community access."},
    {"role_code": "TEAM_LEADER",
     "role_name": "Team Leader",
     "description": "Supervises support workers and coordinates day-to-day service delivery for a group of participants."},
    {"role_code": "SUPPORT_COORD",
     "role_name": "Support Coordinator",
     "description": "Manages participant NDIS plans, builds capacity, and coordinates multiple service providers."},
    {"role_code": "SPEC_SUPPORT_COORD",
     "role_name": "Specialist Support Coordinator",
     "description": "Provides intensive coordination for participants with complex needs or in crisis situations."},
    {"role_code": "PROG_MANAGER",
     "role_name": "Program Manager",
     "description": "Oversees program operations, quality, compliance, staffing and KPI reporting."},
    {"role_code": "FINANCE_OFFICER",
     "role_name": "Finance Officer",
     "description": "Manages invoicing, NDIS claiming, budget tracking and financial compliance."},
    {"role_code": "HR_OFFICER",
     "role_name": "HR Officer",
     "description": "Manages staff recruitment, onboarding, training records, and HR compliance."},
    {"role_code": "COMPLIANCE_MGR",
     "role_name": "Compliance Manager",
     "description": "Oversees NDIS Practice Standards, audit readiness, and incident management."},
    {"role_code": "IT_SUPPORT",
     "role_name": "IT Support",
     "description": "Manages system access, IT infrastructure and technical support for staff."},
    {"role_code": "BEHAVIOUR_SUPPORT",
     "role_name": "Behaviour Support Practitioner",
     "description": "Assesses behaviours of concern and develops positive behaviour support plans."},
]

# ── Role → permission assignments ─────────────────────────────────────────────
ROLE_PERMS = {
    "SUPPORT_WORKER": [
        "participants:view", "participants:create",
        "schedules:view", "schedules:create",
        "progress_notes:view", "progress_notes:create",
        "incidents:view", "incidents:create",
        "documents:view",
    ],
    "TEAM_LEADER": [
        "participants:view", "participants:create", "participants:edit",
        "schedules:view", "schedules:create", "schedules:edit",
        "progress_notes:view", "progress_notes:create", "progress_notes:edit",
        "incidents:view", "incidents:create", "incidents:edit",
        "documents:view", "documents:create",
        "reports:view",
        "users:view",
    ],
    "SUPPORT_COORD": [
        "participants:view", "participants:create", "participants:edit",
        "plans:view", "plans:create", "plans:edit",
        "schedules:view", "schedules:create", "schedules:edit",
        "progress_notes:view", "progress_notes:create",
        "incidents:view", "incidents:create",
        "documents:view", "documents:create",
        "reports:view", "reports:create",
        "invoices:view",
    ],
    "SPEC_SUPPORT_COORD": [
        "participants:view", "participants:create", "participants:edit",
        "plans:view", "plans:create", "plans:edit",
        "schedules:view", "schedules:create", "schedules:edit",
        "progress_notes:view", "progress_notes:create", "progress_notes:edit",
        "incidents:view", "incidents:create", "incidents:edit",
        "documents:view", "documents:create", "documents:edit",
        "reports:view", "reports:create",
        "invoices:view",
    ],
    "PROG_MANAGER": [
        "participants:view", "participants:create", "participants:edit",
        "plans:view", "plans:create", "plans:edit",
        "schedules:view", "schedules:create", "schedules:edit",
        "progress_notes:view", "progress_notes:create", "progress_notes:edit",
        "incidents:view", "incidents:create", "incidents:edit",
        "documents:view", "documents:create", "documents:edit",
        "reports:view", "reports:create", "reports:edit",
        "invoices:view", "invoices:create",
        "users:view", "users:create", "users:edit",
        "roles:view",
        "branches:view",
        "programs:view",
    ],
    "FINANCE_OFFICER": [
        "invoices:view", "invoices:create", "invoices:edit",
        "reports:view", "reports:create",
        "participants:view",
        "plans:view",
        "documents:view", "documents:create",
    ],
    "HR_OFFICER": [
        "users:view", "users:create", "users:edit",
        "roles:view",
        "documents:view", "documents:create",
        "reports:view",
    ],
    "COMPLIANCE_MGR": [
        "incidents:view", "incidents:create", "incidents:edit", "incidents:delete",
        "documents:view", "documents:create", "documents:edit",
        "reports:view", "reports:create", "reports:edit",
        "participants:view",
        "users:view",
        "roles:view",
        "branches:view",
        "programs:view",
    ],
    "IT_SUPPORT": [
        "users:view", "users:create", "users:edit",
        "roles:view", "roles:create", "roles:edit",
        "branches:view",
        "programs:view",
        "settings:view", "settings:edit",
    ],
    "BEHAVIOUR_SUPPORT": [
        "participants:view", "participants:create", "participants:edit",
        "progress_notes:view", "progress_notes:create", "progress_notes:edit",
        "incidents:view", "incidents:create", "incidents:edit",
        "documents:view", "documents:create", "documents:edit",
        "reports:view", "reports:create",
        "plans:view",
    ],
}


# ════════════════════════════════════════════════════════════
# STEP 1 — Login
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 1  Login\n{SEP2}")

r = requests.post(f"{BASE_URL}/auth/login", json={
    "tenant_code": TENANT_CODE,
    "email":       ADMIN_EMAIL,
    "password":    ADMIN_PASSWORD,
})
if r.status_code != 200:
    fail(f"Login failed {r.status_code}: {r.text[:400]}")

login     = r.json()
TOKEN     = login["access_token"]
TENANT_ID = login["tenant_id"]
HEADERS   = {"Authorization": f"Bearer {TOKEN}"}
ok(f"Logged in as {login['full_name']} (tenant_id={TENANT_ID})")


# ════════════════════════════════════════════════════════════
# STEP 2 — Sync default permissions via API
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 2  Sync Default Permissions\n{SEP2}")

sc, res = api_post(f"/tenant/{TENANT_ID}/permissions/sync")
if sc == 200:
    ok(res.get("message", "Permissions synced"))
else:
    fail(f"Permission sync failed {sc}: {res}")


# ════════════════════════════════════════════════════════════
# STEP 3 — Create roles (skip existing)
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 3  Roles\n{SEP2}")

_, existing_roles = api_get(f"/tenant/{TENANT_ID}/roles")
existing_roles = existing_roles if isinstance(existing_roles, list) else []
existing_role_codes = {r["role_code"] for r in existing_roles}
role_ids = {r["role_code"]: r["role_id"] for r in existing_roles}

for ro in ROLES:
    if ro["role_code"] in existing_role_codes:
        warn(f"Role {ro['role_code']} already exists — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/roles", ro)
    if sc == 201:
        role_ids[ro["role_code"]] = res["role_id"]
        ok(f"Role '{ro['role_name']}' → id={res['role_id']}")
    else:
        warn(f"Role '{ro['role_name']}' failed: {res.get('detail', res)}")

info(f"Total roles available: {len(role_ids)}")


# ════════════════════════════════════════════════════════════
# STEP 4 — Assign permissions to roles
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 4  Role–Permission Assignments\n{SEP2}")

_, all_perms = api_get(f"/tenant/{TENANT_ID}/permissions")
all_perms = all_perms if isinstance(all_perms, list) else []
perm_map = {p["permission_code"]: p["permission_id"] for p in all_perms}
info(f"Found {len(perm_map)} permissions")

for role_code, perm_codes in ROLE_PERMS.items():
    role_id = role_ids.get(role_code)
    if not role_id:
        warn(f"Role {role_code} not found — skipping")
        continue
    assigned = skipped = missing = 0
    for pc in perm_codes:
        pid = perm_map.get(pc)
        if not pid:
            missing += 1
            continue
        sc, res = api_post(f"/tenant/{TENANT_ID}/roles/{role_id}/permissions/{pid}")
        if sc in (200, 201):
            assigned += 1
        elif "already" in str(res.get("detail", "")).lower():
            skipped += 1
        else:
            warn(f"  {pc} → {role_code} failed: {res.get('detail', res)}")
    status_line = f"{assigned} assigned, {skipped} already set"
    if missing:
        status_line += f", {missing} codes not found"
    ok(f"{role_code}: {status_line}")


# ════════════════════════════════════════════════════════════
# DONE
# ════════════════════════════════════════════════════════════
print(f"""
{SEP}
  ROLES & PERMISSIONS SEED COMPLETE
{SEP}
  Tenant ID    : {TENANT_ID}
  Roles seeded : {len(ROLE_PERMS)}
  Permissions  : {len(perm_map)} available in DB

  Open Roles & Permissions in the NDIS Manager frontend to verify.
  Backend docs : http://localhost:8000/docs
{SEP}
""")
