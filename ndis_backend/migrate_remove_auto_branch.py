"""
One-time migration:
  1. Makes ndis_common.app_user.branch_id nullable (removes NOT NULL constraint)
  2. Clears branch_id on all admin users who were assigned the auto-created HO-01 branch
  3. Deletes the auto-created "HO-01" Head Office branch from every tenant schema

Run once from the ndis_backend directory:
    python migrate_remove_auto_branch.py

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

    # ── 1. Make branch_id nullable in ndis_common.app_user ───────────────────
    print("\n[1] Making app_user.branch_id nullable…")
    try:
        cursor.execute("""
            ALTER TABLE [ndis_common].[app_user]
            ALTER COLUMN branch_id INT NULL
        """)
        print("   ✓  branch_id is now nullable")
    except Exception as e:
        if "already" in str(e).lower() or "no effect" in str(e).lower():
            print("   ✓  Already nullable, skipping")
        else:
            print(f"   ⚠  {e} — may already be nullable, continuing")

    # ── 2. Per-tenant: clear admin user branch_id + delete HO-01 branch ──────
    cursor.execute(
        "SELECT tenant_id, tenant_code, organisation_name FROM [ndis_common].[tenant] ORDER BY tenant_id"
    )
    tenants = cursor.fetchall()

    for tenant_id, tenant_code, tenant_name in tenants:
        schema = generate_schema_name(tenant_code)

        # Check schema exists
        cursor.execute("SELECT COUNT(*) FROM sys.schemas WHERE name = ?", schema)
        if cursor.fetchone()[0] == 0:
            print(f"\n   ⚠  Schema [{schema}] not found, skipping {tenant_name}")
            continue

        print(f"\n[{tenant_name}] schema=[{schema}]")

        # Find the HO-01 branch
        cursor.execute(f"""
            SELECT branch_id FROM [{schema}].[branch]
            WHERE branch_code = 'HO-01' AND is_deleted = 0
        """)
        row = cursor.fetchone()

        if not row:
            print("   ✓  No HO-01 auto-branch found, skipping")
            continue

        ho_branch_id = row[0]
        print(f"   Found HO-01 branch (id={ho_branch_id})")

        # Clear branch_id on any user pointing to HO-01
        cursor.execute("""
            UPDATE [ndis_common].[app_user]
            SET branch_id = NULL
            WHERE tenant_id = ? AND branch_id = ?
        """, tenant_id, ho_branch_id)
        rows_cleared = cursor.rowcount
        print(f"   ✓  Cleared branch_id on {rows_cleared} user(s)")

        # Delete the HO-01 branch
        cursor.execute(f"""
            DELETE FROM [{schema}].[branch] WHERE branch_id = ?
        """, ho_branch_id)
        print(f"   ✓  Deleted HO-01 branch")

    conn.commit()
    conn.close()

    print("\n✅  Migration complete.")
    print("⚠️  Restart the backend to apply model changes and clear the Redis cache.")


if __name__ == "__main__":
    main()
