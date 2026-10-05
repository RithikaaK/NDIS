"""
Seed sample branch data for the first tenant in the database.

Run from the ndis_backend directory:
    python seed_branches.py

Uses Windows Authentication (Trusted_Connection) — no password needed.
"""
import pyodbc
import re
import sys

# ── DB connection settings (mirrors app/core/config.py defaults) ───────────────
SERVER   = r".\SQLEXPRESS"
DATABASE = "NDIS_DB"
DRIVER   = "ODBC Driver 17 for SQL Server"

CONN_STR = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

# ── Sample branches ────────────────────────────────────────────────────────────
BRANCHES = [
    # ── Active — Head Office ───────────────────────────────────────────────────
    {
        "branch_code":    "HO-SYD",
        "branch_name":    "Sydney Head Office",
        "phone":          "02 9000 0001",
        "email":          "sydney.ho@ndiscare.com.au",
        "address_line1":  "Level 10, 1 Martin Place",
        "suburb":         "Sydney",
        "state_code":     "NSW",
        "postcode":       "2000",
        "is_head_office": True,
        "is_active":      True,
    },
    # ── Active branches ────────────────────────────────────────────────────────
    {
        "branch_code":    "BR-PAR",
        "branch_name":    "Parramatta Branch",
        "phone":          "02 9635 1100",
        "email":          "parramatta@ndiscare.com.au",
        "address_line1":  "Suite 12, 3 Parramatta Square",
        "suburb":         "Parramatta",
        "state_code":     "NSW",
        "postcode":       "2150",
        "is_head_office": False,
        "is_active":      True,
    },
    {
        "branch_code":    "BR-MEL",
        "branch_name":    "Melbourne CBD Branch",
        "phone":          "03 9600 2200",
        "email":          "melbourne@ndiscare.com.au",
        "address_line1":  "Level 5, 200 Collins Street",
        "suburb":         "Melbourne",
        "state_code":     "VIC",
        "postcode":       "3000",
        "is_head_office": False,
        "is_active":      True,
    },
    {
        "branch_code":    "BR-GEE",
        "branch_name":    "Geelong Branch",
        "phone":          "03 5221 3300",
        "email":          "geelong@ndiscare.com.au",
        "address_line1":  "Unit 4, 80 Malop Street",
        "suburb":         "Geelong",
        "state_code":     "VIC",
        "postcode":       "3220",
        "is_head_office": False,
        "is_active":      True,
    },
    {
        "branch_code":    "BR-BNE",
        "branch_name":    "Brisbane Branch",
        "phone":          "07 3001 4400",
        "email":          "brisbane@ndiscare.com.au",
        "address_line1":  "Level 3, 100 Queen Street",
        "suburb":         "Brisbane City",
        "state_code":     "QLD",
        "postcode":       "4000",
        "is_head_office": False,
        "is_active":      True,
    },
    {
        "branch_code":    "BR-GCS",
        "branch_name":    "Gold Coast Branch",
        "phone":          "07 5501 5500",
        "email":          "goldcoast@ndiscare.com.au",
        "address_line1":  "Suite 3, 18 Orchid Avenue",
        "suburb":         "Surfers Paradise",
        "state_code":     "QLD",
        "postcode":       "4217",
        "is_head_office": False,
        "is_active":      True,
    },
    {
        "branch_code":    "BR-PER",
        "branch_name":    "Perth Branch",
        "phone":          "08 9200 6600",
        "email":          "perth@ndiscare.com.au",
        "address_line1":  "Level 2, 50 St Georges Terrace",
        "suburb":         "Perth",
        "state_code":     "WA",
        "postcode":       "6000",
        "is_head_office": False,
        "is_active":      True,
    },
    {
        "branch_code":    "BR-CBR",
        "branch_name":    "Canberra Branch",
        "phone":          "02 6200 7700",
        "email":          "canberra@ndiscare.com.au",
        "address_line1":  "Level 1, 10 Hobart Place",
        "suburb":         "Canberra",
        "state_code":     "ACT",
        "postcode":       "2600",
        "is_head_office": False,
        "is_active":      True,
    },
    # ── Inactive branches (for filter testing) ─────────────────────────────────
    {
        "branch_code":    "BR-ADL",
        "branch_name":    "Adelaide Branch",
        "phone":          "08 8100 8800",
        "email":          "adelaide@ndiscare.com.au",
        "address_line1":  "Suite 8, 45 Grenfell Street",
        "suburb":         "Adelaide",
        "state_code":     "SA",
        "postcode":       "5000",
        "is_head_office": False,
        "is_active":      False,
    },
    {
        "branch_code":    "BR-HOB",
        "branch_name":    "Hobart Branch",
        "phone":          "03 6200 9900",
        "email":          "hobart@ndiscare.com.au",
        "address_line1":  "Ground Floor, 22 Elizabeth Street",
        "suburb":         "Hobart",
        "state_code":     "TAS",
        "postcode":       "7000",
        "is_head_office": False,
        "is_active":      False,
    },
    {
        "branch_code":    "BR-DAR",
        "branch_name":    "Darwin Branch",
        "phone":          "08 8900 1010",
        "email":          "darwin@ndiscare.com.au",
        "address_line1":  "Suite 1, 45 Mitchell Street",
        "suburb":         "Darwin",
        "state_code":     "NT",
        "postcode":       "0800",
        "is_head_office": False,
        "is_active":      False,
    },
]


def generate_schema_name(tenant_code: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9]", "_", tenant_code).lower()
    safe = re.sub(r"_+", "_", safe).strip("_")
    return f"tenant_{safe}"


def main():
    print("Connecting to SQL Server…")
    try:
        conn = pyodbc.connect(CONN_STR, autocommit=False)
    except Exception as e:
        print(f"❌  Connection failed: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    # ── 1. Find the first tenant ───────────────────────────────────────────────
    cursor.execute("SELECT TOP 1 tenant_id, tenant_code, tenant_name FROM [ndis_common].[tenant] ORDER BY tenant_id")
    row = cursor.fetchone()
    if not row:
        print("❌  No tenant found in ndis_common.tenant — sign up first.")
        conn.close()
        sys.exit(1)

    tenant_id, tenant_code, tenant_name = row
    schema = generate_schema_name(tenant_code)
    print(f"✓  Tenant: [{tenant_id}] {tenant_name}  →  schema: [{schema}]")

    # ── 2. Check schema exists ─────────────────────────────────────────────────
    cursor.execute(
        "SELECT COUNT(*) FROM sys.schemas WHERE name = ?", schema
    )
    if cursor.fetchone()[0] == 0:
        print(f"❌  Schema [{schema}] does not exist. Run the app first to provision it.")
        conn.close()
        sys.exit(1)

    # ── 3. Insert branches (skip if branch_code already exists) ───────────────
    inserted = 0
    skipped  = 0

    for b in BRANCHES:
        # Check duplicate
        cursor.execute(
            f"SELECT COUNT(*) FROM [{schema}].[branch] WHERE branch_code = ?",
            b["branch_code"]
        )
        if cursor.fetchone()[0] > 0:
            print(f"   skipping  {b['branch_code']} — already exists")
            skipped += 1
            continue

        cursor.execute(f"""
            INSERT INTO [{schema}].[branch]
                (branch_code, branch_name, phone, email,
                 address_line1, suburb, state_code, postcode,
                 is_head_office, is_active, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            b["branch_code"],
            b["branch_name"],
            b["phone"],
            b["email"],
            b["address_line1"],
            b["suburb"],
            b["state_code"],
            b["postcode"],
            1 if b["is_head_office"] else 0,
            1 if b["is_active"] else 0,
        )
        print(f"   ✓  inserted {b['branch_code']} — {b['branch_name']}")
        inserted += 1

    conn.commit()
    conn.close()

    print(f"\nDone — {inserted} inserted, {skipped} skipped.")
    if inserted > 0:
        print("⚠️  Restart the backend (or wait 5 min) to clear the Redis branch cache.")


if __name__ == "__main__":
    main()
