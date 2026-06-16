"""Authentication router: register, login, and identity introspection."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister
from app.schemas.user import UserRead
from app.services import user_service
from app.services.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (self-service)",
)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> UserRead:
    """Create a new user account with the client role.

    Returns 409 if the email is already registered.
    """
    try:
        return user_service.register_user(db, payload)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.post(
    "/login",
    response_model=Token,
    summary="Exchange credentials for an access token",
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Verify credentials and return a JWT access token.

    Returns 401 with a generic message on failure (regardless of whether
    the email is unknown or the password is wrong) to prevent
    user enumeration.
    """
    try:
        user = user_service.authenticate_user(db, payload.email, payload.password)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    settings = get_settings()
    token = create_access_token(subject=user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Return the currently authenticated user",
)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return identity information for the holder of the bearer token.

    Useful for clients to verify their token is valid and to fetch
    the user's role for UI gating.
    """
    return current_user
