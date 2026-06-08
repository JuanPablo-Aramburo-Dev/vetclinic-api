"""Pet model.

A Pet belongs to a Client (owner). Soft delete via is_active to
preserve medical history even after a pet leaves the clinic.
"""

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Species(str, enum.Enum):
    """Species of a pet."""

    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    RABBIT = "rabbit"
    OTHER = "other"


class Sex(str, enum.Enum):
    """Sex of a pet. UNKNOWN allows registering pets whose sex
    is not yet confirmed."""

    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class Pet(Base, TimestampMixin):
    """A pet owned by a Client."""

    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[Species] = mapped_column(
        SQLEnum(
            Species,
            name="pet_species",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    breed: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sex: Mapped[Sex] = mapped_column(
        SQLEnum(
            Sex,
            name="pet_sex",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    birth_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Owner relationship (many-to-one).
    # ondelete=CASCADE: deleting a Client deletes all their pets.
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # FKs benefit from explicit index for join performance
    )
    owner: Mapped["Client"] = relationship(back_populates="pets")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Pet id={self.id} name={self.name!r} "
            f"species={self.species.value} owner_id={self.owner_id}>"
        )