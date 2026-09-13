"""
RBAC helper — role-based permission checks used in route handlers.
Usage:
    require_roles("ADMINISTRATOR", "PARSER_DEVELOPER")(current_user)
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status

from backend.app.core.dependencies import dep_current_user

ADMIN = "ADMINISTRATOR"
PARSER_DEV = "PARSER_DEVELOPER"
SEC_ANALYST = "SECURITY_ANALYST"
VIEWER = "VIEWER"

# All valid role names
ALL_ROLES = {ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER}


def require_roles(*roles: str) -> Callable[..., Any]:
    """
    FastAPI dependency factory.
    Raises 403 if the current user does not hold at least one of the given roles.
    """
    async def checker(
        current_user: Any = Depends(dep_current_user),
    ) -> Any:
        if current_user.is_superuser:
            return current_user
        user_roles = set(current_user.role_names)
        if not user_roles.intersection(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Operation requires one of: {list(roles)}. "
                    f"Your roles: {list(user_roles)}"
                ),
            )
        return current_user

    return checker


def get_primary_role(user: Any) -> str:
    """Return the highest-privilege role the user holds."""
    priority = [ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER]
    for role in priority:
        if role in user.role_names:
            return role
    return VIEWER
