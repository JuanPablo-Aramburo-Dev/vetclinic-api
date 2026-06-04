"""Client service: business logic for Client operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from app.services.exceptions import (
    ClientEmailAlreadyExistsError,
    ClientNotFoundError,
)


def get_client(db: Session, client_id: int) -> Client:
    """Fetch a Client by id or raise ClientNotFoundError."""
    client = db.get(Client, client_id)
    if client is None:
        raise ClientNotFoundError(f"Client with id={client_id} not found")
    return client


def list_clients(db: Session, skip: int = 0, limit: int = 50) -> list[Client]:
    """Return a paginated list of Clients ordered by id."""
    stmt = select(Client).order_by(Client.id).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def create_client(db: Session, payload: ClientCreate) -> Client:
    """Create a new Client.

    Raises ClientEmailAlreadyExistsError if the email is taken.
    """
    existing = db.scalar(select(Client).where(Client.email == payload.email))
    if existing is not None:
        raise ClientEmailAlreadyExistsError(
            f"Client with email={payload.email!r} already exists"
        )

    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(
    db: Session,
    client_id: int,
    payload: ClientUpdate,
) -> Client:
    """Partially update a Client.

    Only fields explicitly provided in payload are updated.
    Raises ClientNotFoundError if the client does not exist,
    or ClientEmailAlreadyExistsError if the new email belongs to another client.
    """
    client = get_client(db, client_id)

    # exclude_unset=True: only fields the client actually sent in the request.
    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != client.email:
        existing = db.scalar(
            select(Client).where(Client.email == update_data["email"])
        )
        if existing is not None and existing.id != client_id:
            raise ClientEmailAlreadyExistsError(
                f"Client with email={update_data['email']!r} already exists"
            )

    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_id: int) -> None:
    """Delete a Client by id.

    Raises ClientNotFoundError if the client does not exist.
    """
    client = get_client(db, client_id)
    db.delete(client)
    db.commit()