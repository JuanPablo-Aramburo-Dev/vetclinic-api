"""Pydantic schemas for the User resource.

Schemas define the API contract: what clients can send (input) and what
the API returns (output). They are intentionally distinct from the
SQLAlchemy models, which define the database contract.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Fields shared by input and output schemas."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole


class UserCreate(UserBase):
    """Schema for creating a new user.

    Includes the plain password from the client. The service layer will
    hash it before persisting; the hash never appears in any schema.
    """

    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    """Schema for returning a user to the client.

    Crucially excludes hashed_password.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime