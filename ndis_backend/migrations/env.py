"""Alembic environment configuration for NDIS Management System.

Architecture:
  - ndis_common  : Central/unique schema — tracked by Alembic autogenerate.
  - tenant_<id>  : Per-tenant schemas — created at signup via provision_tenant_schema(),
                   NOT tracked by Alembic (dynamic names make static migrations impossible).
  - dbo          : alembic_version table lives here (MSSQL default).

Migration workflow:
  alembic stamp head        — mark existing DB as up-to-date without running DDL
  alembic upgrade head      — apply pending migration scripts
  alembic revision --autogenerate -m "description"  — generate a new migration
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

# ── Make app modules importable from the project root ────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings   # noqa: E402
from app.database import Base          # noqa: E402
import app.models                       # noqa: E402, F401 — registers all models via __init__

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# NOTE: DATABASE_URL contains URL-encoded % characters that configparser
# misinterprets as interpolation syntax.  We pass the engine directly
# (run_migrations_online) or set url= (run_migrations_offline) rather than
# using config.set_main_option("sqlalchemy.url", ...).
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic compares this metadata against the live DB for --autogenerate
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Restrict autogenerate to ndis_common schema tables only.

    Excludes:
      - tenant_schema (placeholder) — per-tenant schemas are provisioned at runtime
      - dbo — MSSQL system default schema
      - Any other schema not explicitly managed by Alembic
    """
    if type_ == "table":
        schema = getattr(object, "schema", None)
        return schema == "ndis_common"
    return True


def run_migrations_offline() -> None:
    """Offline mode: generate SQL script without a live DB connection."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online mode: connect to the DB and run migrations directly."""
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
