"""Client model.

A Client represents the owner of one or more pets. A Client may have an
associated User account for login, but this is optional (walk-in clients
registered by staff have no User).
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.models.user import User


class Client(Base, TimestampMixin):
    """Pet owner."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 1:1 optional relationship with User.
    # ondelete="SET NULL": if the User is deleted, the Client survives
    # but loses its login (becomes walk-in).
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    # ORM-level navigation. The string "User" avoids circular imports
    # if the relationship is ever defined from User's side too.
    user: Mapped[User | None] = relationship("User")

    pets: Mapped[list["Pet"]] = relationship(  # noqa: F821
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Client id={self.id} " f"name={self.first_name!r} {self.last_name!r}>"
