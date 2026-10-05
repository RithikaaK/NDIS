"""
Clear dummy address data from the auto-created Head Office branch.

This fixes existing tenants whose Head Office branch was created with
placeholder values ("Sydney", "NSW", etc.) during signup.

Run from the ndis_backend directory:
    python clear_dummy_branch_data.py

Uses Windows Authentication — no password needed.
"""
import pyodbc
import re
import sys

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

# These are the dummy values we want to clear (only if they look like placeholders)
DUMMY_ADDRESS  = "1 Main Street"
DUMMY_SUBURB   = "Sydney"
DUMMY_STATE    = "NSW"
DUMMY_POSTCODE = "2000"


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

    # Find all tenants
    cursor.execute(
        "SELECT tenant_id, tenant_code, organisation_name FROM [ndis_common].[tenant] ORDER BY tenant_id"
    )
    tenants = cursor.fetchall()

    if not tenants:
        print("No tenants found.")
        conn.close()
        return

    total_updated = 0

    for tenant_id, tenant_code, tenant_name in tenants:
        schema = generate_schema_name(tenant_code)

        # Check schema exists
        cursor.execute("SELECT COUNT(*) FROM sys.schemas WHERE name = ?", schema)
        if cursor.fetchone()[0] == 0:
            print(f"   ⚠  Schema [{schema}] not found, skipping tenant {tenant_name}")
            continue

        # Find head office branches that still have dummy address data
        cursor.execute(f"""
            SELECT branch_id, branch_name, address_line1, suburb, state_code, postcode
            FROM [{schema}].[branch]
            WHERE is_head_office = 1 AND is_deleted = 0
        """)
        branches = cursor.fetchall()

        for branch_id, branch_name, addr1, suburb, state, postcode in branches:
            fields_to_clear = {}

            if addr1 == DUMMY_ADDRESS:
                fields_to_clear['address_line1'] = None
            if suburb == DUMMY_SUBURB:
                fields_to_clear['suburb'] = None
            if state == DUMMY_STATE:
                fields_to_clear['state_code'] = None
            if postcode == DUMMY_POSTCODE:
                fields_to_clear['postcode'] = None

            if not fields_to_clear:
                print(f"   ✓  [{tenant_name}] Branch '{branch_name}' — no dummy data found, skipping")
                continue

            set_clause = ", ".join(f"{col} = NULL" for col in fields_to_clear)
            cursor.execute(f"""
                UPDATE [{schema}].[branch]
                SET {set_clause}
                WHERE branch_id = ?
            """, branch_id)

            cleared = ", ".join(fields_to_clear.keys())
            print(f"   ✓  [{tenant_name}] Branch '{branch_name}' — cleared: {cleared}")
            total_updated += 1

    conn.commit()
    conn.close()

    print(f"\nDone — {total_updated} branch(es) updated.")
    if total_updated > 0:
        print("⚠️  Restart the backend (or wait 5 min) to clear the Redis branch cache.")


if __name__ == "__main__":
    main()
