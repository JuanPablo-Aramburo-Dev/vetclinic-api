"""Pet service: business logic for Pet operations.

Pets use soft delete (is_active flag) to preserve medical history.
Listings default to active-only; individual lookups return the pet
regardless of active state.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.pet import Pet
from app.schemas.pet import PetCreate, PetUpdate
from app.services.exceptions import (
    OwnerNotFoundError,
    PetNotFoundError,
)


def get_pet(db: Session, pet_id: int) -> Pet:
    """Fetch a Pet by id regardless of is_active state.

    Returning inactive pets allows the API to expose medical history.
    Raises PetNotFoundError if the pet does not exist at all.
    """
    pet = db.get(Pet, pet_id)
    if pet is None:
        raise PetNotFoundError(f"Pet with id={pet_id} not found")
    return pet


def list_pets(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
) -> list[Pet]:
    """Return a paginated list of Pets ordered by id.

    By default only active pets are returned. Pass include_inactive=True
    to retrieve all pets (useful for historical reports).
    """
    stmt = select(Pet).order_by(Pet.id).offset(skip).limit(limit)
    if not include_inactive:
        stmt = stmt.where(Pet.is_active.is_(True))
    return list(db.scalars(stmt))


def list_pets_by_owner(
    db: Session,
    owner_id: int,
    include_inactive: bool = False,
) -> list[Pet]:
    """Return all pets belonging to a specific Client.

    Raises OwnerNotFoundError if the owner does not exist (to disambiguate
    from a legitimately empty result for an existing client).
    """
    owner = db.get(Client, owner_id)
    if owner is None:
        raise OwnerNotFoundError(f"Client with id={owner_id} not found")

    stmt = select(Pet).where(Pet.owner_id == owner_id).order_by(Pet.id)
    if not include_inactive:
        stmt = stmt.where(Pet.is_active.is_(True))
    return list(db.scalars(stmt))


def create_pet(db: Session, payload: PetCreate) -> Pet:
    """Create a new Pet.

    Validates that the owner_id corresponds to an existing Client.
    Raises OwnerNotFoundError otherwise.
    """
    owner = db.get(Client, payload.owner_id)
    if owner is None:
        raise OwnerNotFoundError(
            f"Client with id={payload.owner_id} not found"
        )

    pet = Pet(**payload.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def update_pet(db: Session, pet_id: int, payload: PetUpdate) -> Pet:
    """Partially update a Pet.

    Only fields explicitly provided in payload are updated.
    is_active can be toggled via this endpoint (e.g., to reactivate a pet).
    Raises PetNotFoundError if the pet does not exist.
    """
    pet = get_pet(db, pet_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pet, field, value)
    db.commit()
    db.refresh(pet)
    return pet


def delete_pet(db: Session, pet_id: int) -> Pet:
    """Soft-delete a Pet by setting is_active=False.

    Idempotent: deleting an already-inactive pet is a no-op (no error).
    Returns the pet (now inactive) for the caller's convenience.
    Raises PetNotFoundError if the pet does not exist at all.
    """
    pet = get_pet(db, pet_id)
    if pet.is_active:
        pet.is_active = False
        db.commit()
        db.refresh(pet)
    return pet