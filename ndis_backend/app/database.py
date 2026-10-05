"""Database configuration and asynchronous session management for MSSQL using aioodbc."""
from typing import Any, AsyncGenerator, Dict

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.security import get_current_user

# Asynchronous engine for Microsoft SQL Server using aioodbc
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# Session factory — used for ndis_common schema queries (auth, tenant lookup, signup)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — session for ndis_common schema (platform tables).

    Use for: login, signup, tenant lookup, AppUser CRUD, subscription plans.
    Do NOT use for tenant business data (branches, programs, roles) — use get_tenant_session().
    """
    async with AsyncSessionLocal() as db:
        yield db


async def get_tenant_db(schema_name: str) -> AsyncGenerator[AsyncSession, None]:
    """Low-level helper — async session scoped to a specific tenant schema.

    Uses SQLAlchemy's schema_translate_map to rewrite ORM queries for models
    declared with  schema="tenant_schema"  to the real per-tenant schema:

        schema_translate_map={"tenant_schema": "tenant_sunshi_001"}
        →  SELECT * FROM [tenant_sunshi_001].[branch]

    Prefer using get_tenant_session() as a FastAPI Depends rather than calling
    this directly.

    Args:
        schema_name: System-generated schema name (e.g. "tenant_sunshi_001").
                     Always derived from a trusted authenticated JWT.
    """
    async with engine.connect() as conn:
        conn = await conn.execution_options(
            schema_translate_map={"tenant_schema": schema_name}
        )
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session


async def get_tenant_session(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — tenant-scoped session from the authenticated JWT.

    Reads schema_name from the JWT (embedded at login from Tenant.schema_name)
    and yields an AsyncSession configured with the correct schema_translate_map.

    Security: schema_name is system-generated (from tenant_code) and validated
    by the JWT signature — it is never taken from client request parameters.

    Use for: branches, programs, roles, permissions, user_roles, tenant_config, audit_log.
    """
    schema_name: str | None = current_user.get("schema_name")
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing the schema_name claim — please re-authenticate",
        )
    async for session in get_tenant_db(schema_name):
        yield session
