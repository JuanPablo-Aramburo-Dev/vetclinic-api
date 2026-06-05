"""Integration tests for the Clients REST endpoint."""

from fastapi import status
from fastapi.testclient import TestClient

VALID_PAYLOAD = {
    "first_name": "Juan",
    "last_name": "Aramburo",
    "email": "juan@test.com",
    "phone": "5551234567",
}


class TestListClients:
    """GET /clients/"""

    def test_returns_empty_list_when_no_clients(self, client: TestClient) -> None:
        response = client.get("/clients/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_returns_existing_clients(self, client: TestClient) -> None:
        client.post("/clients/", json=VALID_PAYLOAD)
        response = client.get("/clients/")
        body = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert len(body) == 1
        assert body[0]["email"] == "juan@test.com"


class TestCreateClient:
    """POST /clients/"""

    def test_creates_client_and_returns_201(self, client: TestClient) -> None:
        response = client.post("/clients/", json=VALID_PAYLOAD)
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["id"] == 1
        assert body["email"] == "juan@test.com"
        assert body["address"] is None
        assert body["user_id"] is None
        assert "created_at" in body
        assert "updated_at" in body

    def test_rejects_duplicate_email_with_409(self, client: TestClient) -> None:
        client.post("/clients/", json=VALID_PAYLOAD)
        duplicate = {**VALID_PAYLOAD, "first_name": "Other"}
        response = client.post("/clients/", json=duplicate)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]

    def test_rejects_invalid_email_with_422(self, client: TestClient) -> None:
        bad = {**VALID_PAYLOAD, "email": "not-an-email"}
        response = client.post("/clients/", json=bad)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_rejects_missing_required_field_with_422(self, client: TestClient) -> None:
        incomplete = {"first_name": "X", "email": "a@b.com", "phone": "5551234567"}
        response = client.post("/clients/", json=incomplete)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetClient:
    """GET /clients/{id}"""

    def test_returns_client_when_exists(self, client: TestClient) -> None:
        created = client.post("/clients/", json=VALID_PAYLOAD).json()
        response = client.get(f"/clients/{created['id']}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == "juan@test.com"

    def test_returns_404_when_missing(self, client: TestClient) -> None:
        response = client.get("/clients/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


class TestUpdateClient:
    """PATCH /clients/{id}"""

    def test_updates_only_provided_fields(self, client: TestClient) -> None:
        created = client.post("/clients/", json=VALID_PAYLOAD).json()
        response = client.patch(
            f"/clients/{created['id']}",
            json={"first_name": "Juan Pablo"},
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["first_name"] == "Juan Pablo"
        # Other fields unchanged.
        assert body["last_name"] == "Aramburo"
        assert body["email"] == "juan@test.com"

    def test_returns_404_when_missing(self, client: TestClient) -> None:
        response = client.patch("/clients/9999", json={"first_name": "X"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_taking_existing_email_with_409(self, client: TestClient) -> None:
        client.post("/clients/", json=VALID_PAYLOAD)
        second = {
            "first_name": "Other",
            "last_name": "Person",
            "email": "other@test.com",
            "phone": "5559999999",
        }
        second_created = client.post("/clients/", json=second).json()
        response = client.patch(
            f"/clients/{second_created['id']}",
            json={"email": "juan@test.com"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT


class TestDeleteClient:
    """DELETE /clients/{id}"""

    def test_deletes_client_and_returns_204(self, client: TestClient) -> None:
        created = client.post("/clients/", json=VALID_PAYLOAD).json()
        response = client.delete(f"/clients/{created['id']}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Confirm it's gone.
        get_response = client.get(f"/clients/{created['id']}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_when_missing(self, client: TestClient) -> None:
        response = client.delete("/clients/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
