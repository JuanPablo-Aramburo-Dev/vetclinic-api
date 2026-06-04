"""SQLAlchemy declarative base for all ORM models.

All models in the application should inherit from `Base`.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    Using SQLAlchemy 2.0's DeclarativeBase. All models that inherit
    from this will be registered with Base.metadata, which is what
    Alembic uses to detect schema changes.
    """

    pass