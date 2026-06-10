"""Pydantic schemas for authentication endpoints.

Distinct from app.schemas.user.UserCreate because the public registration
endpoint must not expose the `role` field; otherwise any client could
self-assign administrator privileges (a mass assignment vulnerability).
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Public registration payload.

    Does NOT accept `role`: all self-registered users become regular
    clients. Staff accounts (admin, vet) must be created through an
    administrative channel, not implemented in this iteration.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Login payload."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Token(BaseModel):
    """OAuth 2.0-style bearer token response.

    The client must send the access_token in the Authorization header
    as `Bearer <token>` for protected endpoints.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until the token expires")