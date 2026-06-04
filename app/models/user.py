"""User model.

Represents authenticated identities in the system. Both Clients and
Veterinarians may have an associated User account for login purposes,
but a Client can also exist without one (walk-in customers registered
by staff).
"""

import enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class UserRole(str, enum.Enum):
    """Role of a user within the system."""

    ADMIN = "admin"
    VET = "vet"
    CLIENT = "client"


class User(Base, TimestampMixin):
    """User account for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role.value}>"
