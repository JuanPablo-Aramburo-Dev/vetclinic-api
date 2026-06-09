"""HTTP router for the Pet resource."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.pet import PetCreate, PetRead, PetUpdate
from app.services import pet_service
from app.services.exceptions import OwnerNotFoundError, PetNotFoundError

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get(
    "/",
    response_model=list[PetRead],
    summary="List pets",
)
def list_pets(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[PetRead]:
    """Return a paginated list of pets.

    By default only active pets are returned. Pass include_inactive=true
    to include soft-deleted pets (e.g., for historical reports).
    """
    return pet_service.list_pets(db, skip=skip, limit=limit, include_inactive=include_inactive)


@router.get(
    "/{pet_id}",
    response_model=PetRead,
    summary="Get a pet by id",
)
def get_pet(pet_id: int, db: Session = Depends(get_db)) -> PetRead:
    """Return a single pet by id.

    Returns the pet regardless of its is_active state (medical history
    is preserved and queryable even after soft delete).
    """
    try:
        return pet_service.get_pet(db, pet_id)
    except PetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/",
    response_model=PetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pet",
)
def create_pet(
    payload: PetCreate,
    db: Session = Depends(get_db),
) -> PetRead:
    """Create a new pet. The referenced owner_id must exist."""
    try:
        return pet_service.create_pet(db, payload)
    except OwnerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@router.patch(
    "/{pet_id}",
    response_model=PetRead,
    summary="Partially update a pet",
)
def update_pet(
    pet_id: int,
    payload: PetUpdate,
    db: Session = Depends(get_db),
) -> PetRead:
    """Update only the fields provided.

    Setting is_active=true can be used to reactivate a soft-deleted pet.
    """
    try:
        return pet_service.update_pet(db, pet_id, payload)
    except PetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.delete(
    "/{pet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a pet",
)
def delete_pet(pet_id: int, db: Session = Depends(get_db)) -> None:
    """Soft-delete a pet by marking it as inactive.

    Idempotent: calling on an already-inactive pet is a no-op.
    """
    try:
        pet_service.delete_pet(db, pet_id)
    except PetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# Nested endpoint: pets of a specific client.
# Mounted under /clients/{client_id}/pets/ via a separate router instance
# that is registered in main.py.
clients_pets_router = APIRouter(
    prefix="/clients/{client_id}/pets",
    tags=["pets"],
)


@clients_pets_router.get(
    "/",
    response_model=list[PetRead],
    summary="List pets of a specific client",
)
def list_pets_by_owner(
    client_id: int,
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[PetRead]:
    """Return all pets belonging to the specified client.

    Returns 404 if the client does not exist (to distinguish from
    a legitimately empty list).
    """
    try:
        return pet_service.list_pets_by_owner(db, client_id, include_inactive=include_inactive)
    except OwnerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
