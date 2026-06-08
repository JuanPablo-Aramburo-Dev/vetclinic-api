"""Pydantic schemas for the Pet resource."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.pet import Sex, Species


class PetBase(BaseModel):
    """Fields shared by input and output schemas."""

    name: str = Field(min_length=1, max_length=100)
    species: Species
    breed: str | None = Field(default=None, max_length=100)
    sex: Sex
    birth_date: date | None = None
    weight_kg: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("999.99"),
        decimal_places=2,
    )

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_in_future(cls, v: date | None) -> date | None:
        """Birth date cannot be in the future."""
        if v is not None and v > date.today():
            raise ValueError("birth_date cannot be in the future")
        return v


class PetCreate(PetBase):
    """Schema for creating a new pet.

    Includes owner_id (which Client this pet belongs to).
    is_active is intentionally excluded; new pets are always active.
    """

    owner_id: int = Field(gt=0)


class PetUpdate(BaseModel):
    """Schema for partial updates (PATCH).

    All fields optional. Does not inherit from PetBase so all fields
    can be optional. owner_id is excluded; transferring ownership
    should be a dedicated operation, not a casual PATCH.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    species: Species | None = None
    breed: str | None = Field(default=None, max_length=100)
    sex: Sex | None = None
    birth_date: date | None = None
    weight_kg: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("999.99"),
        decimal_places=2,
    )
    is_active: bool | None = None

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_in_future(cls, v: date | None) -> date | None:
        """Birth date cannot be in the future."""
        if v is not None and v > date.today():
            raise ValueError("birth_date cannot be in the future")
        return v


class PetRead(PetBase):
    """Schema for returning a pet to the API consumer."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime