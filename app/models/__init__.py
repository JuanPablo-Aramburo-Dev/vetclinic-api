"""SQLAlchemy ORM models.

All models are imported here so that Base.metadata is fully populated
when Alembic introspects the schema.
"""

from app.models.client import Client
from app.models.user import User, UserRole

__all__ = ["Client", "User", "UserRole"]
