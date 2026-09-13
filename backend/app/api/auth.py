"""
Authentication API.
POST /api/v1/auth/login  — issue JWT
GET  /api/v1/auth/me     — return current user
POST /api/v1/auth/users  — create user (ADMIN only)
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.audit.audit_service import AuditService
from backend.app.core.dependencies import DepDB, dep_current_user
from backend.app.core.exceptions import AuthenticationError
from backend.app.core.logging import actor_var
from backend.app.core.rbac import ADMIN, require_roles
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.audit_log import AuditAction
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.auth import TokenResponse, UserCreate, UserResponse

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenResponse)
async def login(
    db: DepDB,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """Authenticate and return a JWT access token."""
    repo = UserRepository(db)
    user = await repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    extra_claims = {"roles": user.role_names}
    token = create_access_token(subject=user.id, extra_claims=extra_claims)

    # Audit
    actor_var.set(user.username)
    audit = AuditService(db)
    await audit.record(
        actor=user.username,
        actor_role=user.role_names[0] if user.role_names else None,
        action=AuditAction.USER_LOGIN,
        resource_type="user",
        resource_id=user.username,
    )

    from backend.app.core.config import get_settings
    settings = get_settings()
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[object, Depends(dep_current_user)],
) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> UserResponse:
    """Create a new user (ADMINISTRATOR only)."""
    repo = UserRepository(db)

    # Check uniqueness
    if await repo.get_by_username(data.username):
        raise HTTPException(status_code=409, detail=f"Username '{data.username}' is taken")
    if await repo.get_by_email(data.email):
        raise HTTPException(status_code=409, detail=f"Email '{data.email}' is registered")

    user = await repo.create(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )

    # Assign role
    role = await repo.get_role_by_name(data.role)
    if not role:
        role = await repo.create_role(data.role)
    await repo.assign_role(user.id, role.id)

    # Audit
    audit = AuditService(db)
    await audit.record(
        actor=current_user.username,  # type: ignore[attr-defined]
        actor_role="ADMINISTRATOR",
        action=AuditAction.USER_CREATED,
        resource_type="user",
        resource_id=user.username,
    )

    # Reload with roles
    user = await repo.get_by_id(user.id)  # type: ignore[assignment]
    return UserResponse.model_validate(user)
