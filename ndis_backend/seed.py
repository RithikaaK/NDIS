#!/usr/bin/env python3
"""
seed.py — Populates Sunshine NDIS full sample data via the REST API.

Prerequisites:
  1. Backend running:  uvicorn app.main:app --reload
  2. pip install requests  (or: pip install requests --break-system-packages)

Usage:
  cd C:\\new\\ndis_backend
  python seed.py
"""
import sys
import requests

BASE_URL       = "http://localhost:8000/api/v1"
ADMIN_EMAIL    = "john.smith@sunshine-ndis.com.au"
ADMIN_PASSWORD = "Admin@1234"
ORG_ABN        = "51824753556"
EXPECTED_CODE  = "SUNSHI-001"

SEP  = "═" * 60
SEP2 = "─" * 60


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
    try:    data = r.json(); return r.status_code, data if isinstance(data, list) else data
    except: return r.status_code, []


def api_put(path, body):
    r = requests.put(f"{BASE_URL}{path}", json=body, headers=HEADERS)
    try:    return r.status_code, r.json()
    except: return r.status_code, {"detail": r.text}


# Placeholder so the global name exists before login
HEADERS = {}

# ════════════════════════════════════════════════════════════
# STEP 1 — Register tenant
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 1  Register Tenant\n{SEP2}")

r = requests.post(f"{BASE_URL}/tenant/signup/registered", json={
    "organisation_name": "Sunshine NDIS Services Pty Ltd",
    "trading_name":      "Sunshine NDIS",
    "abn":               ORG_ABN,
    "primary_email":     "info@sunshine-ndis.com.au",
    "primary_phone":     "02 9000 1000",
    "ndis_registration_number": "4050000001",
    "admin_first_name":  "John",
    "admin_last_name":   "Smith",
    "admin_email":       ADMIN_EMAIL,
    "admin_password":    ADMIN_PASSWORD,
    "admin_job_title":   "Chief Executive Officer",
    "admin_mobile":      "0400 000 001",
    "head_office_address_line1": "Level 5, 100 Market Street",
    "head_office_suburb":        "Sydney",
    "head_office_state_code":    "NSW",
    "head_office_postcode":      "2000",
})

if r.status_code == 201:
    TENANT_CODE = r.json()["tenant_code"]
    ok(f"Tenant created — code: {TENANT_CODE}")
elif r.status_code == 409:
    warn("Tenant already exists (ABN conflict). Using expected code.")
    TENANT_CODE = EXPECTED_CODE
else:
    fail(f"Signup failed {r.status_code}: {r.text[:400]}")


# ════════════════════════════════════════════════════════════
# STEP 2 — Login and get JWT
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 2  Login\n{SEP2}")

r = requests.post(f"{BASE_URL}/auth/login", json={
    "tenant_code": TENANT_CODE,
    "email":       ADMIN_EMAIL,
    "password":    ADMIN_PASSWORD,
})
if r.status_code != 200:
    fail(f"Login failed {r.status_code}: {r.text[:400]}")

login       = r.json()
TOKEN       = login["access_token"]
TENANT_ID   = login["tenant_id"]
SCHEMA_NAME = login.get("schema_name", "(unknown)")
HEADERS     = {"Authorization": f"Bearer {TOKEN}"}
ok(f"Logged in as {login['full_name']} (tenant_id={TENANT_ID})")
info(f"Tenant schema: {SCHEMA_NAME}")


# ════════════════════════════════════════════════════════════
# STEP 3 — Branches
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 3  Branches\n{SEP2}")

BRANCHES = [
    {
        "branch_code": "SYD-CBD",
        "branch_name": "Sydney CBD Office",
        "phone":       "02 9000 1001",
        "email":       "sydney@sunshine-ndis.com.au",
        "address_line1": "Level 3, 50 George Street",
        "suburb":      "Sydney",
        "state_code":  "NSW",
        "postcode":    "2000",
        "is_head_office": True,
        "is_active":   True,
    },
    {
        "branch_code": "SYD-WEST",
        "branch_name": "Western Sydney Office",
        "phone":       "02 9000 1002",
        "email":       "westsydney@sunshine-ndis.com.au",
        "address_line1": "Shop 5, 120 Victoria Road",
        "suburb":      "Parramatta",
        "state_code":  "NSW",
        "postcode":    "2150",
        "is_head_office": False,
        "is_active":   True,
    },
    {
        "branch_code": "MEL-CBD",
        "branch_name": "Melbourne CBD Office",
        "phone":       "03 9000 2001",
        "email":       "melbourne@sunshine-ndis.com.au",
        "address_line1": "Suite 12, 200 Collins Street",
        "suburb":      "Melbourne",
        "state_code":  "VIC",
        "postcode":    "3000",
        "is_head_office": False,
        "is_active":   True,
    },
    {
        "branch_code": "MEL-EAST",
        "branch_name": "Eastern Melbourne Office",
        "phone":       "03 9000 2002",
        "email":       "eastmelb@sunshine-ndis.com.au",
        "address_line1": "Unit 3, 45 Maroondah Highway",
        "suburb":      "Ringwood",
        "state_code":  "VIC",
        "postcode":    "3134",
        "is_head_office": False,
        "is_active":   True,
    },
    {
        "branch_code": "BNE-CBD",
        "branch_name": "Brisbane CBD Office",
        "phone":       "07 3000 3001",
        "email":       "brisbane@sunshine-ndis.com.au",
        "address_line1": "Level 8, 300 Queen Street",
        "suburb":      "Brisbane City",
        "state_code":  "QLD",
        "postcode":    "4000",
        "is_head_office": False,
        "is_active":   True,
    },
]

_, existing_branches = api_get(f"/tenant/{TENANT_ID}/branches")
existing_branches = existing_branches if isinstance(existing_branches, list) else []
existing_branch_codes = {b["branch_code"] for b in existing_branches}
branch_ids = {b["branch_code"]: b["branch_id"] for b in existing_branches}

for b in BRANCHES:
    if b["branch_code"] in existing_branch_codes:
        warn(f"Branch {b['branch_code']} already exists — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/branches", b)
    if sc == 201:
        branch_ids[b["branch_code"]] = res["branch_id"]
        ok(f"Branch '{b['branch_name']}' → id={res['branch_id']}")
    else:
        warn(f"Branch '{b['branch_name']}' failed: {res.get('detail', res)}")

_, all_branches = api_get(f"/tenant/{TENANT_ID}/branches")
for ab in (all_branches if isinstance(all_branches, list) else []):
    branch_ids.setdefault(ab["branch_code"], ab["branch_id"])

if not branch_ids:
    fail("No branches exist — cannot continue")

DEFAULT_BID = (branch_ids.get("SYD-CBD")
               or branch_ids.get("HO-01")
               or next(iter(branch_ids.values())))
info(f"Default branch id = {DEFAULT_BID}")


# ════════════════════════════════════════════════════════════
# STEP 4 — Programs
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 4  Programs\n{SEP2}")

PROGRAMS = [
    {"program_code": "SC-001", "program_name": "Support Coordination",
     "funding_type": "Support Coordination",
     "description": "Helps participants implement their NDIS plan and connect with providers."},
    {"program_code": "SC-002", "program_name": "Specialist Support Coordination",
     "funding_type": "Support Coordination",
     "description": "Specialist coordination for participants with complex support needs."},
    {"program_code": "DA-001", "program_name": "Daily Activities",
     "funding_type": "Daily Activities",
     "description": "Assistance with daily personal activities including hygiene, dressing and meals."},
    {"program_code": "CA-001", "program_name": "Community Access",
     "funding_type": "Community Access",
     "description": "Support to access and participate in the local community."},
    {"program_code": "TH-001", "program_name": "Therapy Services",
     "funding_type": "Therapy",
     "description": "Allied health including OT, physiotherapy, speech therapy and psychology."},
    {"program_code": "SIL-001", "program_name": "Supported Independent Living",
     "funding_type": "Accommodation",
     "description": "24/7 support in a shared or individual living environment."},
    {"program_code": "STA-001", "program_name": "Short Term Accommodation",
     "funding_type": "Accommodation",
     "description": "Respite and short-term supported accommodation for participants."},
    {"program_code": "EM-001", "program_name": "Employment Support",
     "funding_type": "Employment",
     "description": "Support to find and maintain employment in the open workforce."},
    {"program_code": "BEH-001", "program_name": "Behaviour Support",
     "funding_type": "Behaviour Support",
     "description": "Specialist behaviour support and positive behaviour support planning."},
    {"program_code": "TECH-001", "program_name": "Assistive Technology",
     "funding_type": "Capital Supports",
     "description": "Assessment, trial and implementation of assistive technology solutions."},
]

_, existing_programs = api_get(f"/tenant/{TENANT_ID}/programs")
existing_programs = existing_programs if isinstance(existing_programs, list) else []
existing_prog_codes = {p["program_code"] for p in existing_programs}
program_ids = {p["program_code"]: p["program_id"] for p in existing_programs}

for p in PROGRAMS:
    if p["program_code"] in existing_prog_codes:
        warn(f"Program {p['program_code']} already exists — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/programs", p)
    if sc == 201:
        program_ids[p["program_code"]] = res["program_id"]
        ok(f"Program '{p['program_name']}' → id={res['program_id']}")
    else:
        warn(f"Program '{p['program_name']}' failed: {res.get('detail', res)}")


# ════════════════════════════════════════════════════════════
# STEP 5 — Program ↔ Branch Assignments
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 5  Program–Branch Assignments\n{SEP2}")

# Map programs to which branches deliver them
PROG_BRANCH_MAP = {
    "SC-001":  ["SYD-CBD", "MEL-CBD", "BNE-CBD"],
    "SC-002":  ["SYD-CBD", "MEL-CBD"],
    "DA-001":  ["SYD-CBD", "SYD-WEST", "MEL-CBD", "MEL-EAST", "BNE-CBD"],
    "CA-001":  ["SYD-CBD", "SYD-WEST", "MEL-CBD", "MEL-EAST", "BNE-CBD"],
    "TH-001":  ["SYD-CBD", "MEL-CBD", "BNE-CBD"],
    "SIL-001": ["SYD-CBD", "SYD-WEST", "MEL-CBD"],
    "STA-001": ["SYD-CBD", "MEL-CBD", "BNE-CBD"],
    "EM-001":  ["SYD-CBD", "MEL-CBD"],
    "BEH-001": ["SYD-CBD", "MEL-CBD"],
    "TECH-001":["SYD-CBD", "MEL-CBD", "BNE-CBD"],
}

for prog_code, branch_codes in PROG_BRANCH_MAP.items():
    prog_id = program_ids.get(prog_code)
    if not prog_id:
        warn(f"Program {prog_code} not found — skipping branch assignments")
        continue
    for bc in branch_codes:
        bid = branch_ids.get(bc)
        if not bid:
            warn(f"  Branch {bc} not found — skipping")
            continue
        sc, res = api_post(f"/tenant/{TENANT_ID}/programs/{prog_id}/branches/{bid}")
        if sc in (200, 201):
            ok(f"{prog_code} → {bc}")
        elif "already assigned" in str(res.get("detail", "")):
            info(f"{prog_code} → {bc} (already assigned)")
        else:
            warn(f"{prog_code} → {bc} failed: {res.get('detail', res)}")


# ════════════════════════════════════════════════════════════
# STEP 6 — Roles
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 6  Roles\n{SEP2}")

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


# ════════════════════════════════════════════════════════════
# STEP 7 — Role–Permission Assignments
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 7  Role–Permission Assignments\n{SEP2}")

_, all_perms = api_get(f"/tenant/{TENANT_ID}/permissions")
all_perms = all_perms if isinstance(all_perms, list) else []
perm_map = {p["permission_code"]: p["permission_id"] for p in all_perms}
info(f"Found {len(perm_map)} system permissions")

# Which permission codes each role gets
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

for role_code, perm_codes in ROLE_PERMS.items():
    role_id = role_ids.get(role_code)
    if not role_id:
        warn(f"Role {role_code} not found — skipping permissions")
        continue
    assigned = 0
    skipped  = 0
    for pc in perm_codes:
        pid = perm_map.get(pc)
        if not pid:
            continue   # permission not seeded yet — skip silently
        sc, res = api_post(
            f"/tenant/{TENANT_ID}/roles/{role_id}/permissions/{pid}"
        )
        if sc in (200, 201):
            assigned += 1
        elif "already" in str(res.get("detail", "")).lower():
            skipped += 1
        else:
            warn(f"  {pc} → {role_code} failed: {res.get('detail', res)}")
    ok(f"{role_code}: {assigned} permissions assigned, {skipped} already set")


# ════════════════════════════════════════════════════════════
# STEP 8 — Users
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 8  Users\n{SEP2}")

syd  = branch_ids.get("SYD-CBD",  DEFAULT_BID)
syd2 = branch_ids.get("SYD-WEST", DEFAULT_BID)
mel  = branch_ids.get("MEL-CBD",  DEFAULT_BID)
mel2 = branch_ids.get("MEL-EAST", DEFAULT_BID)
bne  = branch_ids.get("BNE-CBD",  DEFAULT_BID)

USERS = [
    # Support Workers
    {"first_name": "Sarah",   "last_name": "Johnson",
     "email": "sarah.johnson@sunshine-ndis.com.au",
     "password": "Worker@1234", "mobile": "0400 100 001",
     "job_title": "Support Worker", "branch_id": syd,
     "is_tenant_admin": False, "_roles": ["SUPPORT_WORKER"]},
    {"first_name": "James",   "last_name": "Nguyen",
     "email": "james.nguyen@sunshine-ndis.com.au",
     "password": "Worker@1234", "mobile": "0400 100 002",
     "job_title": "Support Worker", "branch_id": syd2,
     "is_tenant_admin": False, "_roles": ["SUPPORT_WORKER"]},
    {"first_name": "Aisha",   "last_name": "Mohamed",
     "email": "aisha.mohamed@sunshine-ndis.com.au",
     "password": "Worker@1234", "mobile": "0400 100 003",
     "job_title": "Support Worker", "branch_id": mel,
     "is_tenant_admin": False, "_roles": ["SUPPORT_WORKER"]},
    {"first_name": "Connor",  "last_name": "Walsh",
     "email": "connor.walsh@sunshine-ndis.com.au",
     "password": "Worker@1234", "mobile": "0400 100 004",
     "job_title": "Support Worker", "branch_id": mel2,
     "is_tenant_admin": False, "_roles": ["SUPPORT_WORKER"]},
    {"first_name": "Mei",     "last_name": "Zhang",
     "email": "mei.zhang@sunshine-ndis.com.au",
     "password": "Worker@1234", "mobile": "0400 100 005",
     "job_title": "Support Worker", "branch_id": bne,
     "is_tenant_admin": False, "_roles": ["SUPPORT_WORKER"]},
    # Team Leaders
    {"first_name": "Michael", "last_name": "Chen",
     "email": "michael.chen@sunshine-ndis.com.au",
     "password": "Leader@1234", "mobile": "0400 200 001",
     "job_title": "Team Leader", "branch_id": syd,
     "is_tenant_admin": False, "_roles": ["TEAM_LEADER"]},
    {"first_name": "Rachel",  "last_name": "Thompson",
     "email": "rachel.thompson@sunshine-ndis.com.au",
     "password": "Leader@1234", "mobile": "0400 200 002",
     "job_title": "Team Leader", "branch_id": mel,
     "is_tenant_admin": False, "_roles": ["TEAM_LEADER"]},
    # Support Coordinators
    {"first_name": "Emily",   "last_name": "Williams",
     "email": "emily.williams@sunshine-ndis.com.au",
     "password": "Coord@1234", "mobile": "0400 300 001",
     "job_title": "Support Coordinator", "branch_id": syd,
     "is_tenant_admin": False, "_roles": ["SUPPORT_COORD"]},
    {"first_name": "Lucas",   "last_name": "Martin",
     "email": "lucas.martin@sunshine-ndis.com.au",
     "password": "Coord@1234", "mobile": "0400 300 002",
     "job_title": "Support Coordinator", "branch_id": mel,
     "is_tenant_admin": False, "_roles": ["SUPPORT_COORD"]},
    {"first_name": "Priya",   "last_name": "Patel",
     "email": "priya.patel@sunshine-ndis.com.au",
     "password": "Coord@1234", "mobile": "0400 300 003",
     "job_title": "Specialist Support Coordinator", "branch_id": bne,
     "is_tenant_admin": False, "_roles": ["SPEC_SUPPORT_COORD"]},
    # Program Manager
    {"first_name": "David",   "last_name": "Brown",
     "email": "david.brown@sunshine-ndis.com.au",
     "password": "Manager@12", "mobile": "0400 400 001",
     "job_title": "Program Manager", "branch_id": syd,
     "is_tenant_admin": False, "_roles": ["PROG_MANAGER"]},
    # Finance
    {"first_name": "Linda",   "last_name": "Kovacs",
     "email": "linda.kovacs@sunshine-ndis.com.au",
     "password": "Finance@12", "mobile": "0400 500 001",
     "job_title": "Finance Officer", "branch_id": syd,
     "is_tenant_admin": False, "_roles": ["FINANCE_OFFICER"]},
    # Compliance
    {"first_name": "Nathan",  "last_name": "O'Brien",
     "email": "nathan.obrien@sunshine-ndis.com.au",
     "password": "Comply@123", "mobile": "0400 600 001",
     "job_title": "Compliance Manager", "branch_id": syd,
     "is_tenant_admin": False, "_roles": ["COMPLIANCE_MGR"]},
    # Behaviour Support
    {"first_name": "Sophie",  "last_name": "Davis",
     "email": "sophie.davis@sunshine-ndis.com.au",
     "password": "Behave@123", "mobile": "0400 700 001",
     "job_title": "Behaviour Support Practitioner", "branch_id": mel,
     "is_tenant_admin": False, "_roles": ["BEHAVIOUR_SUPPORT"]},
]

_, existing_users = api_get(f"/tenant/{TENANT_ID}/users")
existing_users = existing_users if isinstance(existing_users, list) else []
existing_emails = {u["email"] for u in existing_users}

for u in USERS:
    roles_to_assign = u.pop("_roles")
    if u["email"] in existing_emails:
        warn(f"User {u['email']} already exists — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/users", u)
    if sc == 201:
        uid = res["user_id"]
        ok(f"{u['first_name']} {u['last_name']} ({u['job_title']}) → {uid}")
        for rc in roles_to_assign:
            rid = role_ids.get(rc)
            if rid:
                rs, rr = api_post(f"/tenant/{TENANT_ID}/users/{uid}/roles/{rid}")
                if rs in (200, 201):
                    ok(f"  └─ Role '{rc}' assigned")
                else:
                    warn(f"  └─ Role assign failed: {rr.get('detail', rr)}")
    else:
        warn(f"{u['first_name']} {u['last_name']} failed: {res.get('detail', res)}")


# ════════════════════════════════════════════════════════════
# STEP 9 — Contacts
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 9  Contacts\n{SEP2}")

CONTACTS = [
    {
        "tenant_id":     TENANT_ID,
        "contact_type":  "Primary",
        "first_name":    "John",
        "last_name":     "Smith",
        "position_title":"Chief Executive Officer",
        "email":         ADMIN_EMAIL,
        "phone":         "02 9000 1000",
        "mobile":        "0400 000 001",
    },
    {
        "tenant_id":     TENANT_ID,
        "contact_type":  "Billing",
        "first_name":    "Linda",
        "last_name":     "Kovacs",
        "position_title":"Finance Officer",
        "email":         "linda.kovacs@sunshine-ndis.com.au",
        "phone":         "02 9000 1010",
        "mobile":        "0400 500 001",
    },
    {
        "tenant_id":     TENANT_ID,
        "contact_type":  "Compliance",
        "first_name":    "Nathan",
        "last_name":     "O'Brien",
        "position_title":"Compliance Manager",
        "email":         "nathan.obrien@sunshine-ndis.com.au",
        "phone":         "02 9000 1020",
        "mobile":        "0400 600 001",
    },
]

_, existing_contacts = api_get(f"/tenant/{TENANT_ID}/contacts")
existing_contacts = existing_contacts if isinstance(existing_contacts, list) else []
existing_contact_types = {c["contact_type"] for c in existing_contacts}

for c in CONTACTS:
    if c["contact_type"] in existing_contact_types:
        warn(f"Contact type '{c['contact_type']}' already exists — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/contacts", c)
    if sc == 201:
        ok(f"Contact '{c['contact_type']}' — {c['first_name']} {c['last_name']}")
    else:
        warn(f"Contact '{c['contact_type']}' failed: {res.get('detail', res)}")


# ════════════════════════════════════════════════════════════
# STEP 10 — Addresses
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 10  Addresses\n{SEP2}")

ADDRESSES = [
    {
        "tenant_id":    TENANT_ID,
        "address_type": "Head Office",
        "address_line1":"Level 5, 100 Market Street",
        "suburb":       "Sydney",
        "state_code":   "NSW",
        "postcode":     "2000",
        "country":      "Australia",
        "is_primary":   True,
    },
    {
        "tenant_id":    TENANT_ID,
        "address_type": "Registered",
        "address_line1":"Level 5, 100 Market Street",
        "suburb":       "Sydney",
        "state_code":   "NSW",
        "postcode":     "2000",
        "country":      "Australia",
        "is_primary":   False,
    },
    {
        "tenant_id":    TENANT_ID,
        "address_type": "Mailing",
        "address_line1":"PO Box 1234",
        "suburb":       "Sydney",
        "state_code":   "NSW",
        "postcode":     "2001",
        "country":      "Australia",
        "is_primary":   False,
    },
]

_, existing_addresses = api_get(f"/tenant/{TENANT_ID}/addresses")
existing_addresses = existing_addresses if isinstance(existing_addresses, list) else []
existing_addr_types = {a["address_type"] for a in existing_addresses}

for a in ADDRESSES:
    if a["address_type"] in existing_addr_types:
        warn(f"Address type '{a['address_type']}' already exists — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/addresses", a)
    if sc == 201:
        ok(f"Address '{a['address_type']}' — {a['address_line1']}, {a['suburb']}")
    else:
        warn(f"Address '{a['address_type']}' failed: {res.get('detail', res)}")


# ════════════════════════════════════════════════════════════
# STEP 11 — Service States
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 11  Service States\n{SEP2}")

SERVICE_STATES = [
    {"tenant_id": TENANT_ID, "state_code": "NSW"},
    {"tenant_id": TENANT_ID, "state_code": "VIC"},
    {"tenant_id": TENANT_ID, "state_code": "QLD"},
    {"tenant_id": TENANT_ID, "state_code": "ACT"},
]

_, existing_states = api_get(f"/tenant/{TENANT_ID}/service-states")
existing_states = existing_states if isinstance(existing_states, list) else []
existing_state_codes = {s["state_code"] for s in existing_states}

for s in SERVICE_STATES:
    if s["state_code"] in existing_state_codes:
        warn(f"State {s['state_code']} already registered — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/service-states", s)
    if sc == 201:
        ok(f"Service state: {s['state_code']}")
    else:
        warn(f"State {s['state_code']} failed: {res.get('detail', res)}")


# ════════════════════════════════════════════════════════════
# STEP 12 — Registration Groups
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 12  NDIS Registration Groups\n{SEP2}")

REG_GROUPS = [
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0104",
     "registration_group_name": "High Intensity Daily Personal Activities"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0106",
     "registration_group_name": "Assistance in Supported Independent Living"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0107",
     "registration_group_name": "Participate Community"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0108",
     "registration_group_name": "Assistance with Travel/Transport Arrangements"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0110",
     "registration_group_name": "Daily Activities"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0115",
     "registration_group_name": "Assistance with Daily Life Tasks in a Group or Shared Living Arrangement"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0117",
     "registration_group_name": "Specialist Support Coordination"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0128",
     "registration_group_name": "Therapeutic Supports"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0136",
     "registration_group_name": "Group and Centre Based Activities"},
    {"tenant_id": TENANT_ID,
     "registration_group_code": "0207",
     "registration_group_name": "Support Coordination"},
]

_, existing_rgs = api_get(f"/tenant/{TENANT_ID}/registration-groups")
existing_rgs = existing_rgs if isinstance(existing_rgs, list) else []
existing_rg_codes = {rg["registration_group_code"] for rg in existing_rgs}

for rg in REG_GROUPS:
    if rg["registration_group_code"] in existing_rg_codes:
        warn(f"Reg group {rg['registration_group_code']} already exists — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/registration-groups", rg)
    if sc == 201:
        ok(f"[{rg['registration_group_code']}] {rg['registration_group_name']}")
    else:
        warn(f"Reg group {rg['registration_group_code']} failed: {res.get('detail', res)}")


# ════════════════════════════════════════════════════════════
# STEP 13 — Tenant Config
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 13  Tenant Configuration\n{SEP2}")

sc, existing_cfg = api_get(f"/tenant/{TENANT_ID}/config")
if sc == 200 and existing_cfg:
    sc2, res2 = api_put(f"/tenant/{TENANT_ID}/config", {
        "date_format":              "DD/MM/YYYY",
        "currency_code":            "AUD",
        "enable_gst":               True,
        "enable_schads_award":      True,
        "enable_pace_integration":  False,
        "enable_proda_integration": False,
        "default_funding_type":     "Agency Managed",
        "invoice_prefix":           "SUN",
        "invoice_due_days":         14,
    })
    if sc2 == 200:
        ok("Tenant config updated (prefix=SUN, 14-day terms, GST=on)")
    else:
        warn(f"Config update failed: {res2.get('detail', res2)}")
else:
    warn("Config endpoint returned unexpected result — skipping")


# ════════════════════════════════════════════════════════════
# STEP 14 — Documents
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 14  Documents\n{SEP2}")

DOCUMENTS = [
    {
        "tenant_id":         TENANT_ID,
        "document_category": "Registration",
        "document_name":     "NDIS Provider Registration Certificate 2024–2026",
        "file_path":         "/documents/registration/ndis_certificate_2024.pdf",
        "file_size_kb":      420,
        "mime_type":         "application/pdf",
        "expiry_date":       "2026-06-30",
        "uploaded_by":       "SYSTEM",
    },
    {
        "tenant_id":         TENANT_ID,
        "document_category": "Insurance",
        "document_name":     "Public Liability Insurance Certificate of Currency",
        "file_path":         "/documents/insurance/public_liability_2025.pdf",
        "file_size_kb":      185,
        "mime_type":         "application/pdf",
        "expiry_date":       "2025-12-31",
        "uploaded_by":       "SYSTEM",
    },
    {
        "tenant_id":         TENANT_ID,
        "document_category": "Insurance",
        "document_name":     "Professional Indemnity Insurance Certificate",
        "file_path":         "/documents/insurance/prof_indemnity_2025.pdf",
        "file_size_kb":      192,
        "mime_type":         "application/pdf",
        "expiry_date":       "2025-12-31",
        "uploaded_by":       "SYSTEM",
    },
    {
        "tenant_id":         TENANT_ID,
        "document_category": "Policy",
        "document_name":     "Participant Rights and Responsibilities Policy",
        "file_path":         "/documents/policies/participant_rights_v3.pdf",
        "file_size_kb":      310,
        "mime_type":         "application/pdf",
        "expiry_date":       None,
        "uploaded_by":       "SYSTEM",
    },
    {
        "tenant_id":         TENANT_ID,
        "document_category": "Policy",
        "document_name":     "Incident Management and Reporting Policy",
        "file_path":         "/documents/policies/incident_management_v2.pdf",
        "file_size_kb":      275,
        "mime_type":         "application/pdf",
        "expiry_date":       None,
        "uploaded_by":       "SYSTEM",
    },
    {
        "tenant_id":         TENANT_ID,
        "document_category": "Compliance",
        "document_name":     "NDIS Quality & Safeguards Self-Assessment 2024",
        "file_path":         "/documents/compliance/self_assessment_2024.xlsx",
        "file_size_kb":      890,
        "mime_type":         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "expiry_date":       None,
        "uploaded_by":       "SYSTEM",
    },
    {
        "tenant_id":         TENANT_ID,
        "document_category": "ABN",
        "document_name":     "ABN Registration Confirmation",
        "file_path":         "/documents/legal/abn_confirmation.pdf",
        "file_size_kb":      95,
        "mime_type":         "application/pdf",
        "expiry_date":       None,
        "uploaded_by":       "SYSTEM",
    },
]

_, existing_docs = api_get(f"/tenant/{TENANT_ID}/documents")
existing_docs = existing_docs if isinstance(existing_docs, list) else []
existing_doc_names = {d["document_name"] for d in existing_docs}

for d in DOCUMENTS:
    if d["document_name"] in existing_doc_names:
        warn(f"Document '{d['document_name'][:45]}...' already exists — skipping")
        continue
    sc, res = api_post(f"/tenant/{TENANT_ID}/documents", d)
    if sc == 201:
        ok(f"[{d['document_category']}] {d['document_name'][:50]}")
    else:
        warn(f"Document failed: {res.get('detail', res)}")


# ════════════════════════════════════════════════════════════
# DONE
# ════════════════════════════════════════════════════════════
print(f"""
{SEP}
  SEED COMPLETE — Sunshine NDIS Services
{SEP}
  Tenant code   : {TENANT_CODE}
  Tenant ID     : {TENANT_ID}
  Tenant schema : {SCHEMA_NAME}

  Admin login
  ├─ Email      : {ADMIN_EMAIL}
  └─ Password   : {ADMIN_PASSWORD}

  Staff logins (all passwords below)
  ├─ Support Workers     : Worker@1234
  ├─ Team Leaders        : Leader@1234
  ├─ Support Coordinators: Coord@1234
  ├─ Program Manager     : Manager@12
  ├─ Finance Officer     : Finance@12
  └─ Compliance Manager  : Comply@123

  Backend docs  : http://localhost:8000/docs
  Frontend      : http://localhost:5173
{SEP}
""")
