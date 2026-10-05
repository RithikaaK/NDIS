"""Security utilities: password hashing, JWT token handling, and authentication dependencies."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import anyio
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# CryptContext using bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme — shows a clean "Bearer token" input in Swagger UI
http_bearer = HTTPBearer(auto_error=True)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password (sync — use verify_password_async in async contexts)."""
    return pwd_context.verify(plain_password, hashed_password)


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Async-safe bcrypt verify — runs in a thread so it never blocks the event loop."""
    return await anyio.to_thread.run_sync(
        lambda: pwd_context.verify(plain_password, hashed_password),
        cancellable=True,
    )


def get_password_hash(password: str) -> str:
    """Hashes a plain-text password using bcrypt (sync — use get_password_hash_async in async contexts)."""
    return pwd_context.hash(password)


async def get_password_hash_async(password: str) -> str:
    """Async-safe bcrypt hash — runs in a thread so it never blocks the event loop."""
    return await anyio.to_thread.run_sync(
        lambda: pwd_context.hash(password),
        cancellable=True,
    )


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a signed JWT access token.

    Expected keys in data:
      - 'sub'            : user_id (string)
      - 'tenant_id'      : tenant_id (integer)
      - 'schema_name'    : per-tenant schema name e.g. "tenant_sunshi_001" (string)
      - 'email'          : user email (string)
      - 'is_tenant_admin': bool
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token, returning its payload."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> Dict[str, Any]:
    """Dependency that extracts and validates the authenticated user from the JWT.

    Returns:
        dict with keys:
          - user_id     : str
          - tenant_id   : int
          - schema_name : str  — the per-tenant MSSQL schema name (system-generated)
    """
    payload = decode_access_token(credentials.credentials)
    user_id: Optional[str] = payload.get("sub")
    tenant_id: Optional[int] = payload.get("tenant_id")
    schema_name: Optional[str] = payload.get("schema_name")

    if not user_id or not tenant_id or not schema_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing required identity claims (sub, tenant_id, schema_name)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": str(user_id),
        "tenant_id": int(tenant_id),
        "schema_name": str(schema_name),
    }
