"""Integration tests for the Clients REST endpoint.

All client endpoints are protected: the suite uses `authenticated_client`
(a TestClient with a Bearer token pre-applied). A separate test verifies
that requests without a token return 401.
"""

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

    def test_returns_empty_list_when_no_clients(self, authenticated_client: TestClient) -> None:
        response = authenticated_client.get("/clients/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_returns_existing_clients(self, authenticated_client: TestClient) -> None:
        authenticated_client.post("/clients/", json=VALID_PAYLOAD)
        response = authenticated_client.get("/clients/")
        body = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert len(body) == 1
        assert body[0]["email"] == "juan@test.com"


class TestCreateClient:
    """POST /clients/"""

    def test_creates_client_and_returns_201(self, authenticated_client: TestClient) -> None:
        response = authenticated_client.post("/clients/", json=VALID_PAYLOAD)
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["id"] == 1
        assert body["email"] == "juan@test.com"
        assert body["address"] is None
        assert body["user_id"] is None
        assert "created_at" in body
        assert "updated_at" in body

    def test_rejects_duplicate_email_with_409(self, authenticated_client: TestClient) -> None:
        authenticated_client.post("/clients/", json=VALID_PAYLOAD)
        duplicate = {**VALID_PAYLOAD, "first_name": "Other"}
        response = authenticated_client.post("/clients/", json=duplicate)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]

    def test_rejects_invalid_email_with_422(self, authenticated_client: TestClient) -> None:
        bad = {**VALID_PAYLOAD, "email": "not-an-email"}
        response = authenticated_client.post("/clients/", json=bad)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_rejects_missing_required_field_with_422(
        self, authenticated_client: TestClient
    ) -> None:
        incomplete = {"first_name": "X", "email": "a@b.com", "phone": "5551234567"}
        response = authenticated_client.post("/clients/", json=incomplete)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetClient:
    """GET /clients/{id}"""

    def test_returns_client_when_exists(self, authenticated_client: TestClient) -> None:
        created = authenticated_client.post("/clients/", json=VALID_PAYLOAD).json()
        response = authenticated_client.get(f"/clients/{created['id']}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == "juan@test.com"

    def test_returns_404_when_missing(self, authenticated_client: TestClient) -> None:
        response = authenticated_client.get("/clients/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


class TestUpdateClient:
    """PATCH /clients/{id}"""

    def test_updates_only_provided_fields(self, authenticated_client: TestClient) -> None:
        created = authenticated_client.post("/clients/", json=VALID_PAYLOAD).json()
        response = authenticated_client.patch(
            f"/clients/{created['id']}",
            json={"first_name": "Juan Pablo"},
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["first_name"] == "Juan Pablo"
        # Other fields unchanged.
        assert body["last_name"] == "Aramburo"
        assert body["email"] == "juan@test.com"

    def test_returns_404_when_missing(self, authenticated_client: TestClient) -> None:
        response = authenticated_client.patch("/clients/9999", json={"first_name": "X"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_taking_existing_email_with_409(self, authenticated_client: TestClient) -> None:
        authenticated_client.post("/clients/", json=VALID_PAYLOAD)
        second = {
            "first_name": "Other",
            "last_name": "Person",
            "email": "other@test.com",
            "phone": "5559999999",
        }
        second_created = authenticated_client.post("/clients/", json=second).json()
        response = authenticated_client.patch(
            f"/clients/{second_created['id']}",
            json={"email": "juan@test.com"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT


class TestDeleteClient:
    """DELETE /clients/{id}"""

    def test_deletes_client_and_returns_204(self, authenticated_client: TestClient) -> None:
        created = authenticated_client.post("/clients/", json=VALID_PAYLOAD).json()
        response = authenticated_client.delete(f"/clients/{created['id']}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Confirm it's gone.
        get_response = authenticated_client.get(f"/clients/{created['id']}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_when_missing(self, authenticated_client: TestClient) -> None:
        response = authenticated_client.delete("/clients/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestClientsAuthProtection:
    """Authentication enforcement on /clients/ endpoints.

    A single test per resource is enough to verify the global
    get_current_user dependency is wired up; the OAuth2 scheme produces
    the same 'Not authenticated' response for every protected endpoint.
    """

    def test_returns_401_without_token(self, client: TestClient) -> None:
        response = client.get("/clients/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"
