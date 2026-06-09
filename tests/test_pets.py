"""Integration tests for the Pets endpoint."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _create_client(client: TestClient, email: str = "owner@test.com") -> int:
    """Create a client via the API and return its id."""
    response = client.post(
        "/clients/",
        json={
            "first_name": "Test",
            "last_name": "Owner",
            "email": email,
            "phone": "5550000000",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()["id"]


def _pet_payload(owner_id: int, **overrides) -> dict:
    """Return a valid pet payload, with overrides applied."""
    payload = {
        "name": "Firulais",
        "species": "dog",
        "breed": "Labrador",
        "sex": "male",
        "birth_date": "2020-05-15",
        "weight_kg": "25.50",
        "owner_id": owner_id,
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------------------- #
# Happy path
# --------------------------------------------------------------------------- #
def test_create_pet_returns_201_with_full_data(client: TestClient) -> None:
    owner_id = _create_client(client)
    response = client.post("/pets/", json=_pet_payload(owner_id))

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "Firulais"
    assert body["species"] == "dog"
    assert body["sex"] == "male"
    assert body["breed"] == "Labrador"
    assert body["birth_date"] == "2020-05-15"
    assert body["weight_kg"] == "25.50"
    assert body["owner_id"] == owner_id
    assert body["is_active"] is True
    assert "created_at" in body
    assert "updated_at" in body


def test_get_pet_returns_200(client: TestClient) -> None:
    owner_id = _create_client(client)
    created = client.post("/pets/", json=_pet_payload(owner_id)).json()

    response = client.get(f"/pets/{created['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == created


def test_list_pets_returns_only_active_by_default(client: TestClient) -> None:
    owner_id = _create_client(client)
    active = client.post("/pets/", json=_pet_payload(owner_id, name="Active")).json()
    inactive = client.post("/pets/", json=_pet_payload(owner_id, name="Inactive")).json()
    client.delete(f"/pets/{inactive['id']}")

    response = client.get("/pets/")

    assert response.status_code == status.HTTP_200_OK
    ids = [p["id"] for p in response.json()]
    assert active["id"] in ids
    assert inactive["id"] not in ids


def test_list_pets_with_include_inactive_returns_all(client: TestClient) -> None:
    owner_id = _create_client(client)
    active = client.post("/pets/", json=_pet_payload(owner_id, name="Active")).json()
    inactive = client.post("/pets/", json=_pet_payload(owner_id, name="Inactive")).json()
    client.delete(f"/pets/{inactive['id']}")

    response = client.get("/pets/?include_inactive=true")

    assert response.status_code == status.HTTP_200_OK
    ids = [p["id"] for p in response.json()]
    assert active["id"] in ids
    assert inactive["id"] in ids


def test_update_pet_partial(client: TestClient) -> None:
    owner_id = _create_client(client)
    created = client.post("/pets/", json=_pet_payload(owner_id)).json()

    response = client.patch(f"/pets/{created['id']}", json={"weight_kg": "27.30"})

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["weight_kg"] == "27.30"
    # Other fields must be untouched.
    assert body["name"] == created["name"]
    assert body["species"] == created["species"]
    assert body["breed"] == created["breed"]


def test_soft_delete_pet_returns_204(client: TestClient) -> None:
    owner_id = _create_client(client)
    created = client.post("/pets/", json=_pet_payload(owner_id)).json()

    response = client.delete(f"/pets/{created['id']}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""


def test_soft_deleted_pet_persists_and_can_be_reactivated(
    client: TestClient,
) -> None:
    owner_id = _create_client(client)
    created = client.post("/pets/", json=_pet_payload(owner_id)).json()

    # Soft delete.
    client.delete(f"/pets/{created['id']}")

    # Pet still exists and is_active is False.
    after_delete = client.get(f"/pets/{created['id']}").json()
    assert after_delete["is_active"] is False

    # Reactivate via PATCH.
    reactivated = client.patch(f"/pets/{created['id']}", json={"is_active": True}).json()
    assert reactivated["is_active"] is True


def test_delete_pet_is_idempotent(client: TestClient) -> None:
    owner_id = _create_client(client)
    created = client.post("/pets/", json=_pet_payload(owner_id)).json()

    first = client.delete(f"/pets/{created['id']}")
    second = client.delete(f"/pets/{created['id']}")

    assert first.status_code == status.HTTP_204_NO_CONTENT
    assert second.status_code == status.HTTP_204_NO_CONTENT


# --------------------------------------------------------------------------- #
# 404 cases
# --------------------------------------------------------------------------- #
def test_get_pet_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/pets/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_update_pet_not_found_returns_404(client: TestClient) -> None:
    response = client.patch("/pets/9999", json={"name": "X"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_pet_not_found_returns_404(client: TestClient) -> None:
    response = client.delete("/pets/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --------------------------------------------------------------------------- #
# 422 cases
# --------------------------------------------------------------------------- #
def test_create_pet_with_missing_owner_returns_422(client: TestClient) -> None:
    response = client.post("/pets/", json=_pet_payload(owner_id=9999))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "not found" in response.json()["detail"].lower()


def test_create_pet_with_future_birth_date_returns_422(
    client: TestClient,
) -> None:
    owner_id = _create_client(client)
    future = (date.today() + timedelta(days=30)).isoformat()
    response = client.post("/pets/", json=_pet_payload(owner_id, birth_date=future))

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    body = response.json()
    # Pydantic error structure.
    assert any(err["loc"] == ["body", "birth_date"] for err in body["detail"])


def test_create_pet_with_invalid_species_returns_422(client: TestClient) -> None:
    owner_id = _create_client(client)
    response = client.post(
        "/pets/",
        json=_pet_payload(owner_id, species="dragon"),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_pet_with_negative_weight_returns_422(
    client: TestClient,
) -> None:
    owner_id = _create_client(client)
    response = client.post(
        "/pets/",
        json=_pet_payload(owner_id, weight_kg="-1.00"),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --------------------------------------------------------------------------- #
# Nested endpoint: /clients/{client_id}/pets/
# --------------------------------------------------------------------------- #
def test_list_pets_by_owner_returns_only_that_owners_pets(
    client: TestClient,
) -> None:
    owner_a = _create_client(client, email="a@test.com")
    owner_b = _create_client(client, email="b@test.com")

    pet_a = client.post("/pets/", json=_pet_payload(owner_a, name="A")).json()
    pet_b = client.post("/pets/", json=_pet_payload(owner_b, name="B")).json()

    response = client.get(f"/clients/{owner_a}/pets/")

    assert response.status_code == status.HTTP_200_OK
    ids = [p["id"] for p in response.json()]
    assert pet_a["id"] in ids
    assert pet_b["id"] not in ids


def test_list_pets_by_owner_with_no_pets_returns_empty_list(
    client: TestClient,
) -> None:
    owner_id = _create_client(client)
    response = client.get(f"/clients/{owner_id}/pets/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_list_pets_by_missing_owner_returns_404(client: TestClient) -> None:
    response = client.get("/clients/9999/pets/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()
