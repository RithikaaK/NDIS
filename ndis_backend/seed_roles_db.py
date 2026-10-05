#!/usr/bin/env python3
"""
seed_roles_db.py
────────────────
Directly seeds roles and permissions into an existing NDIS tenant
WITHOUT needing the backend to be running or any login credentials.

Usage:
  cd C:\\new\\ndis_backend
  python seed_roles_db.py

The script auto-detects the tenant schema from the database.
If you have multiple tenants, it lists them and picks the first active one.
Set SEED_SCHEMA env var to target a specific schema.
"""
import os
import sys
import pyodbc

# ── DB config (reads from .env values or defaults) ───────────────────────────
DB_SERVER = os.getenv("DB_SERVER",  r".\SQLEXPRESS")
DB_NAME   = os.getenv("DB_NAME",    "NDIS_DB")
DB_DRIVER = os.getenv("DB_DRIVER",  "ODBC Driver 17 for SQL Server")

CONN_STR = (
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    "Trusted_Connection=yes;"
)

SEP  = "═" * 60
SEP2 = "─" * 60


def ok(msg):   print(f"   ✓  {msg}")
def info(msg): print(f"   →  {msg}")
def warn(msg): print(f"   ⚠  {msg}")
def fail(msg): print(f"   ✗  {msg}"); sys.exit(1)


# ── All NDIS permissions (module:action format) ───────────────────────────────
ALL_PERMISSIONS = [
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

# ── 10 Standard NDIS roles ────────────────────────────────────────────────────
ROLES = [
    ("SUPPORT_WORKER",    "Support Worker",
     "Provides direct support to NDIS participants in daily living activities, personal care, and community access."),
    ("TEAM_LEADER",       "Team Leader",
     "Supervises support workers and coordinates day-to-day service delivery for a group of participants."),
    ("SUPPORT_COORD",     "Support Coordinator",
     "Manages participant NDIS plans, builds capacity, and coordinates multiple service providers."),
    ("SPEC_SUPPORT_COORD","Specialist Support Coordinator",
     "Provides intensive coordination for participants with complex needs or in crisis situations."),
    ("PROG_MANAGER",      "Program Manager",
     "Oversees program operations, quality, compliance, staffing and KPI reporting."),
    ("FINANCE_OFFICER",   "Finance Officer",
     "Manages invoicing, NDIS claiming, budget tracking and financial compliance."),
    ("HR_OFFICER",        "HR Officer",
     "Manages staff recruitment, onboarding, training records, and HR compliance."),
    ("COMPLIANCE_MGR",    "Compliance Manager",
     "Oversees NDIS Practice Standards, audit readiness, and incident management."),
    ("IT_SUPPORT",        "IT Support",
     "Manages system access, IT infrastructure and technical support for staff."),
    ("BEHAVIOUR_SUPPORT", "Behaviour Support Practitioner",
     "Assesses behaviours of concern and develops positive behaviour support plans."),
    ("ADMIN", "Admin",
     "Full system access. Manages users, roles, branches, programs, settings and all operational data."),
]

# ── Role → permission code assignments ───────────────────────────────────────
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
    "ADMIN": [
        "branches:view", "branches:create", "branches:edit", "branches:delete",
        "programs:view", "programs:create", "programs:edit", "programs:delete",
        "roles:view", "roles:create", "roles:edit", "roles:delete",
        "permissions:view", "permissions:assign",
        "users:view", "users:create", "users:edit", "users:delete", "users:role_assign",
        "settings:view", "settings:edit",
        "audit:view",
        "participants:view", "participants:create", "participants:edit", "participants:delete",
        "schedules:view", "schedules:create", "schedules:edit", "schedules:delete",
        "progress_notes:view", "progress_notes:create", "progress_notes:edit", "progress_notes:delete",
        "incidents:view", "incidents:create", "incidents:edit", "incidents:delete",
        "documents:view", "documents:create", "documents:edit", "documents:delete",
        "plans:view", "plans:create", "plans:edit", "plans:delete",
        "reports:view", "reports:create", "reports:edit",
        "invoices:view", "invoices:create", "invoices:edit", "invoices:delete",
    ],
}


# ════════════════════════════════════════════════════════════
# Connect
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  Connecting to database\n{SEP2}")
try:
    db = pyodbc.connect(CONN_STR, autocommit=False)
    cur = db.cursor()
    ok(f"Connected to {DB_SERVER} / {DB_NAME}")
except Exception as e:
    fail(f"Cannot connect to DB: {e}")


# ════════════════════════════════════════════════════════════
# Detect tenant schema
# ════════════════════════════════════════════════════════════
SCHEMA = os.getenv("SEED_SCHEMA", "tenant_testor_001")
if not SCHEMA:
    cur.execute("""
        SELECT t.schema_name, t.tenant_code, t.organisation_name, t.status
        FROM ndis_common.tenant t
        WHERE t.is_deleted = 0 AND t.schema_name IS NOT NULL
        ORDER BY t.tenant_id
    """)
    tenants = cur.fetchall()
    if not tenants:
        fail("No active tenants found in the database")
    print(f"\nFound {len(tenants)} active tenant(s):")
    for i, t in enumerate(tenants):
        print(f"  [{i}] schema={t.schema_name}  code={t.tenant_code}  name={t.organisation_name}  status={t.status}")
    if len(tenants) == 1:
        SCHEMA = tenants[0].schema_name
        ok(f"Auto-selected schema: {SCHEMA}")
    else:
        idx = input("\nEnter the number of the tenant to seed [0]: ").strip() or "0"
        SCHEMA = tenants[int(idx)].schema_name
        ok(f"Selected schema: {SCHEMA}")


# ════════════════════════════════════════════════════════════
# STEP 1 — Sync permissions
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 1  Sync Permissions\n{SEP2}")

cur.execute(f"SELECT permission_code FROM [{SCHEMA}].[permission]")
existing_codes = {row[0] for row in cur.fetchall()}
info(f"Existing permission codes: {len(existing_codes)}")

inserted = 0
for perm_code, module, action, description in ALL_PERMISSIONS:
    if perm_code not in existing_codes:
        cur.execute(
            f"INSERT INTO [{SCHEMA}].[permission] "
            "(permission_code, module, action, description, is_active) "
            "VALUES (?, ?, ?, ?, 1)",
            perm_code, module, action, description
        )
        inserted += 1

db.commit()
ok(f"Inserted {inserted} new permissions ({len(existing_codes)} already existed)")


# ════════════════════════════════════════════════════════════
# STEP 2 — Create roles
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 2  Roles\n{SEP2}")

cur.execute(f"SELECT role_code, role_id, is_deleted FROM [{SCHEMA}].[role]")
all_roles = cur.fetchall()
role_ids = {row[0]: row[1] for row in all_roles}
info(f"Existing roles (including deleted): {len(role_ids)}")

created = restored = 0
for role_code, role_name, description in ROLES:
    if role_code in role_ids:
        # Role exists — restore it if soft-deleted and update name/desc
        cur.execute(
            f"UPDATE [{SCHEMA}].[role] "
            "SET role_name=?, description=?, is_active=1, is_deleted=0, deleted_at=NULL "
            "WHERE role_code=?",
            role_name, description, role_code
        )
        restored += 1
        ok(f"Restored '{role_name}' (role_id={role_ids[role_code]})")
    else:
        cur.execute(
            f"INSERT INTO [{SCHEMA}].[role] "
            "(role_code, role_name, description, is_system_role, is_active, is_deleted) "
            "VALUES (?, ?, ?, 0, 1, 0)",
            role_code, role_name, description
        )
        cur.execute(f"SELECT role_id FROM [{SCHEMA}].[role] WHERE role_code = ?", role_code)
        row = cur.fetchone()
        if row:
            role_ids[role_code] = row[0]
            ok(f"Created '{role_name}' → id={row[0]}")
            created += 1

db.commit()
ok(f"Done — {created} created, {restored} restored/updated")


# ════════════════════════════════════════════════════════════
# STEP 3 — Assign permissions to roles
# ════════════════════════════════════════════════════════════
print(f"\n{SEP}\n  STEP 3  Role–Permission Assignments\n{SEP2}")

# Reload permission map (includes newly inserted ones)
cur.execute(f"SELECT permission_code, permission_id FROM [{SCHEMA}].[permission]")
perm_map = {row[0]: row[1] for row in cur.fetchall()}

# Load existing role_permission assignments
cur.execute(f"SELECT role_id, permission_id FROM [{SCHEMA}].[role_permission]")
existing_rp = {(row[0], row[1]) for row in cur.fetchall()}

total_assigned = 0
total_skipped  = 0

for role_code, perm_codes in ROLE_PERMS.items():
    role_id = role_ids.get(role_code)
    if not role_id:
        warn(f"Role {role_code} not found — skipping")
        continue
    assigned = skipped = 0
    for pc in perm_codes:
        pid = perm_map.get(pc)
        if not pid:
            warn(f"  Permission '{pc}' not in DB — skipping")
            continue
        if (role_id, pid) in existing_rp:
            skipped += 1
            continue
        cur.execute(
            f"INSERT INTO [{SCHEMA}].[role_permission] (role_id, permission_id, granted) "
            "VALUES (?, ?, 1)",
            role_id, pid
        )
        assigned += 1
        existing_rp.add((role_id, pid))
    total_assigned += assigned
    total_skipped  += skipped
    ok(f"{role_code}: {assigned} assigned, {skipped} already set")

db.commit()
db.close()


# ════════════════════════════════════════════════════════════
# DONE
# ════════════════════════════════════════════════════════════
print(f"""
{SEP}
  SEED COMPLETE
{SEP}
  Schema      : {SCHEMA}
  Roles       : {len(role_ids)} total
  Permissions : {total_assigned} newly assigned, {total_skipped} already existed

  Refresh the Roles & Permissions page to see all roles.
{SEP}
""")
