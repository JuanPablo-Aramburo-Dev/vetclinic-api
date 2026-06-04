"""Pydantic schemas for the Client resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientBase(BaseModel):
    """Fields shared by input and output schemas."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    address: str | None = Field(default=None, max_length=255)


class ClientCreate(ClientBase):
    """Schema for creating a new client.

    user_id is intentionally not part of the input. Linking a Client to
    a User happens through a dedicated endpoint or is set automatically
    when a client self-registers.
    """

    pass


class ClientUpdate(BaseModel):
    """Schema for partial updates (PATCH).

    All fields optional. Only provided fields are updated.
    Does not inherit from ClientBase because all fields must be optional.
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    address: str | None = Field(default=None, max_length=255)


class ClientRead(ClientBase):
    """Schema for returning a client to the API consumer."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    created_at: datetime
    updated_at: datetime
