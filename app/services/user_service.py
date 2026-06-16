"""Service layer for User domain operations including authentication."""

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister
from app.services.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

# A valid-looking bcrypt hash used as a decoy when the user lookup
# fails, so that verify_password runs and consumes the same time as
# a real verification. Prevents timing-based user enumeration.
_DUMMY_HASH = "$2b$12$" + "x" * 53


def register_user(db: Session, payload: UserRegister) -> User:
    """Create a new user via public self-service registration.

    All self-registered users get UserRole.CLIENT regardless of any
    payload manipulation, because UserRegister does not expose the
    role field at the schema level.

    Raises:
        UserAlreadyExistsError: if the email is already registered.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise UserAlreadyExistsError(f"User with email {payload.email} already exists")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole.CLIENT,  # Always client for self-service.
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Verify credentials and return the user.

    Always runs verify_password even when the user does not exist,
    to make the response time independent of whether the email is
    registered. This prevents timing-based user enumeration.

    Raises:
        InvalidCredentialsError: if email is unknown or password mismatches.
    """
    user = db.query(User).filter(User.email == email).first()

    hash_to_check = user.hashed_password if user is not None else _DUMMY_HASH
    is_valid = verify_password(password, hash_to_check)

    if user is None or not is_valid:
        raise InvalidCredentialsError("Invalid email or password")

    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    """Fetch a user by id.

    Raises:
        UserNotFoundError: if no user with that id exists.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UserNotFoundError(f"User with id={user_id} not found")
    return user
