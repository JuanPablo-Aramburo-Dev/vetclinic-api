"""HTTP router for the Client resource."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.services import client_service
from app.services.exceptions import (
    ClientEmailAlreadyExistsError,
    ClientNotFoundError,
)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get(
    "/",
    response_model=list[ClientRead],
    summary="List clients",
)
def list_clients(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ClientRead]:
    """Return a paginated list of clients."""
    return client_service.list_clients(db, skip=skip, limit=limit)


@router.get(
    "/{client_id}",
    response_model=ClientRead,
    summary="Get a client by id",
)
def get_client(client_id: int, db: Session = Depends(get_db)) -> ClientRead:
    """Return a single client by id."""
    try:
        return client_service.get_client(db, client_id)
    except ClientNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/",
    response_model=ClientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
) -> ClientRead:
    """Create a new client. Email must be unique."""
    try:
        return client_service.create_client(db, payload)
    except ClientEmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.patch(
    "/{client_id}",
    response_model=ClientRead,
    summary="Partially update a client",
)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
) -> ClientRead:
    """Update only the fields provided in the request body."""
    try:
        return client_service.update_client(db, client_id, payload)
    except ClientNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ClientEmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a client",
)
def delete_client(client_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a client by id."""
    try:
        client_service.delete_client(db, client_id)
    except ClientNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e