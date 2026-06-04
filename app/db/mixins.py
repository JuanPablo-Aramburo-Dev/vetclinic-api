"""Reusable SQLAlchemy mixins.

Mixins are classes that contribute columns/behavior to models
without being a parent in the inheritance tree of the database.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds created_at and updated_at columns to a model.

    - created_at: set once when the row is inserted (server-side default).
    - updated_at: set on insert and updated automatically on every update.

    Using server-side defaults (func.now()) so the database, not Python,
    sets the timestamps. This avoids issues with clock skew and time zones.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )