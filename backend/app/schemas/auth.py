"""Auth Pydantic schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import EmailStr, Field

from backend.app.schemas.common import OrmModel


class LoginRequest(OrmModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(OrmModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RoleResponse(OrmModel):
    id: str
    name: str
    description: str


class UserResponse(OrmModel):
    id: str
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    roles: list[RoleResponse] = []
    created_at: datetime
    updated_at: datetime


class UserCreate(OrmModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = "VIEWER"
