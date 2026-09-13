"""
Register all ORM models with SQLAlchemy metadata.
Alembic env.py imports this module to ensure all tables are discovered.
"""
from backend.app.models.user import User, Role, UserRole  # noqa: F401
from backend.app.models.source import Source  # noqa: F401
from backend.app.models.parser import Parser, ParserVersion  # noqa: F401
from backend.app.models.schema import Schema, SchemaVersion  # noqa: F401
from backend.app.models.mapping import Mapping, MappingVersion  # noqa: F401
from backend.app.models.policy import Policy, PolicyVersion  # noqa: F401
from backend.app.models.service import Service  # noqa: F401
from backend.app.models.config_version import ConfigurationVersion  # noqa: F401
from backend.app.models.audit_log import AuditLog  # noqa: F401
from backend.app.models.replay import ReplayOperation  # noqa: F401

__all__ = [
    "User", "Role", "UserRole",
    "Source",
    "Parser", "ParserVersion",
    "Schema", "SchemaVersion",
    "Mapping", "MappingVersion",
    "Policy", "PolicyVersion",
    "Service",
    "ConfigurationVersion",
    "AuditLog",
    "ReplayOperation",
]
