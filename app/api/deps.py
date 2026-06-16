"""Shared FastAPI dependencies.

Currently contains authentication dependencies that resolve the
current user from a JWT bearer token. Other routers import from this
module rather than from app.api.auth, to avoid coupling unrelated
routers to the auth module's internals.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services import user_service
from app.services.exceptions import UserNotFoundError

# tokenUrl points to our login endpoint; this enables Swagger UI's
# "Authorize" button to obtain a token for testing protected endpoints.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a JWT bearer token.

    Returns 401 if:
    - the Authorization header is missing or malformed,
    - the token is expired, tampered, or not an access token,
    - the user referenced by the token no longer exists,
    - the user has been deactivated (is_active=False).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise credentials_exception from e

    subject = payload.get("sub")
    if subject is None:
        raise credentials_exception

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as e:
        raise credentials_exception from e

    try:
        user = user_service.get_user_by_id(db, user_id)
    except UserNotFoundError as e:
        raise credentials_exception from e

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
