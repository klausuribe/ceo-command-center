"""Shared FastAPI dependencies — current user resolution and auth guards."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from backend.app.core.config import get_settings
from backend.app.core.security import decode_token
from backend.app.core.users import User, get_user


def _oauth2_scheme() -> OAuth2PasswordBearer:
    settings = get_settings()
    return OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


oauth2_scheme = _oauth2_scheme()


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Resolve the authenticated user from the bearer token.

    Raises 401 with a WWW-Authenticate header on any failure.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        username = decode_token(token, expected_type="access")
    except JWTError:
        raise unauthorized from None

    user = get_user(username)
    if user is None:
        raise unauthorized
    return user
