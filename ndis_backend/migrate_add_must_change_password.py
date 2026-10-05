"""
Adds the must_change_password column to ndis_common.app_user.

Run once from the ndis_backend directory:
    python migrate_add_must_change_password.py
"""
import pyodbc
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


def main():
    print("Connecting to SQL Server…")
    try:
        conn = pyodbc.connect(CONN_STR, autocommit=True)
    except Exception as e:
        print(f"❌  Connection failed: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("""
        SELECT COUNT(*) FROM sys.columns c
        JOIN sys.tables  t ON c.object_id = t.object_id
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = 'ndis_common'
          AND t.name = 'app_user'
          AND c.name = 'must_change_password'
    """)

    if cursor.fetchone()[0] > 0:
        print("✓  Column 'must_change_password' already exists — nothing to do.")
    else:
        cursor.execute("""
            ALTER TABLE [ndis_common].[app_user]
            ADD must_change_password BIT NOT NULL DEFAULT 0
        """)
        print("✓  Added 'must_change_password BIT NOT NULL DEFAULT 0' to [ndis_common].[app_user]")

    conn.close()
    print("\n✅  Migration complete. Restart the backend to pick up the changes.")


if __name__ == "__main__":
    main()
