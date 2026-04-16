"""Authentication endpoints: login, refresh, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

from backend.app.core.deps import get_current_user
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from backend.app.core.users import User, get_user
from backend.app.schemas.auth import (
    AccessToken,
    LoginRequest,
    RefreshRequest,
    TokenPair,
    UserOut,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(username: str, password: str) -> TokenPair:
    user = get_user(username)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenPair(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
    )


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest) -> TokenPair:
    """Authenticate with JSON body. Primary entrypoint for the Next.js client."""
    return _issue_tokens(payload.username, payload.password)


@router.post("/token", response_model=TokenPair, include_in_schema=True)
def token(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenPair:
    """OAuth2 password-flow token endpoint (form-encoded).

    Same behavior as /login but accepts application/x-www-form-urlencoded so
    that the Swagger UI "Authorize" dialog can drive the flow natively.
    """
    return _issue_tokens(form_data.username, form_data.password)


@router.post("/refresh", response_model=AccessToken)
def refresh(payload: RefreshRequest) -> AccessToken:
    """Exchange a valid refresh token for a fresh access token."""
    try:
        username = decode_token(payload.refresh_token, expected_type="refresh")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None

    if get_user(username) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )
    return AccessToken(access_token=create_access_token(username))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the currently authenticated user."""
    return UserOut(username=current_user.username, name=current_user.name)
