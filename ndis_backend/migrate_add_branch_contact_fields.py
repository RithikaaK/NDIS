"""
Adds contact person columns to the branch table in every existing tenant schema.

Run once from ndis_backend:
    python migrate_add_branch_contact_fields.py
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

NEW_COLUMNS = [
    ("contact_person", "NVARCHAR(255)"),
    ("contact_title",  "NVARCHAR(150)"),
    ("contact_phone",  "NVARCHAR(20)"),
    ("contact_mobile", "NVARCHAR(20)"),
    ("contact_email",  "NVARCHAR(255)"),
]


def generate_schema_name(tenant_code: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9]", "_", tenant_code).lower()
    safe = re.sub(r"_+", "_", safe).strip("_")
    return f"tenant_{safe}"


def main():
    print("Connecting to SQL Server…")
    try:
        conn = pyodbc.connect(CONN_STR, autocommit=True)
    except Exception as e:
        print(f"❌  Connection failed: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT tenant_id, tenant_code, organisation_name FROM [ndis_common].[tenant] ORDER BY tenant_id"
    )
    tenants = cursor.fetchall()

    for tenant_id, tenant_code, org_name in tenants:
        schema = generate_schema_name(tenant_code)

        cursor.execute("SELECT COUNT(*) FROM sys.schemas WHERE name = ?", schema)
        if cursor.fetchone()[0] == 0:
            print(f"⚠  Schema [{schema}] not found, skipping {org_name}")
            continue

        print(f"\n[{org_name}] schema=[{schema}]")

        for col_name, col_type in NEW_COLUMNS:
            # Check if column already exists
            cursor.execute(f"""
                SELECT COUNT(*) FROM sys.columns c
                JOIN sys.tables t ON c.object_id = t.object_id
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = ? AND t.name = 'branch' AND c.name = ?
            """, schema, col_name)

            if cursor.fetchone()[0] > 0:
                print(f"   ✓  {col_name} already exists, skipping")
            else:
                cursor.execute(f"""
                    ALTER TABLE [{schema}].[branch]
                    ADD {col_name} {col_type} NULL
                """)
                print(f"   ✓  Added {col_name} {col_type} NULL")

    conn.close()
    print("\n✅  Migration complete. Restart the backend to pick up the changes.")


if __name__ == "__main__":
    main()
