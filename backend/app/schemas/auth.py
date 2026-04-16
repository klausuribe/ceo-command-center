"""Pydantic DTOs for auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str
    name: str
