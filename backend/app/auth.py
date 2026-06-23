"""Admin authentication: bcrypt password check + JWT bearer tokens.

Single admin account, credentials from env (see config.py). For a real
deployment with multiple admins this would move to a DB table, but a single
configurable account fits the current scope.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

# Hash the configured password once at import (single dev/admin account).
_ADMIN_HASH = bcrypt.hashpw(settings.admin_password.encode("utf-8"), bcrypt.gensalt())


def verify_credentials(username: str, password: str) -> bool:
    """Check username + password against the configured admin account."""
    if username != settings.admin_username:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), _ADMIN_HASH)


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def get_current_admin(token: str = Depends(oauth2_scheme)) -> str:
    """FastAPI dependency: validate bearer token, return username."""
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效或过期的登录凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_alg]
        )
    except jwt.PyJWTError:
        raise cred_exc
    username = payload.get("sub")
    if username != settings.admin_username:
        raise cred_exc
    return username
