"""Integration tests for authentication endpoints.

Covers /auth/register, /auth/login, and /auth/me, including the
security properties asserted in the design:
- mass assignment prevention,
- user enumeration prevention,
- generic 401 for invalid tokens,
- specific 401 message for disabled accounts.
"""

from datetime import timedelta

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User

REGISTER_PAYLOAD = {
    "email": "newuser@example.com",
    "full_name": "New User",
    "password": "SuperSecret123",
}


# --------------------------------------------------------------------------- #
# POST /auth/register
# --------------------------------------------------------------------------- #
class TestRegister:
    """POST /auth/register"""

    def test_registers_user_and_returns_201(self, client: TestClient) -> None:
        response = client.post("/auth/register", json=REGISTER_PAYLOAD)
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["email"] == REGISTER_PAYLOAD["email"]
        assert body["full_name"] == REGISTER_PAYLOAD["full_name"]
        assert body["role"] == "client"
        assert body["is_active"] is True
        assert "hashed_password" not in body
        assert "password" not in body

    def test_rejects_duplicate_email_with_409(self, client: TestClient) -> None:
        client.post("/auth/register", json=REGISTER_PAYLOAD)
        response = client.post("/auth/register", json=REGISTER_PAYLOAD)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]

    def test_rejects_invalid_email_with_422(self, client: TestClient) -> None:
        bad = {**REGISTER_PAYLOAD, "email": "not-an-email"}
        response = client.post("/auth/register", json=bad)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_rejects_short_password_with_422(self, client: TestClient) -> None:
        bad = {**REGISTER_PAYLOAD, "password": "short"}
        response = client.post("/auth/register", json=bad)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = response.json()
        assert any(err["loc"] == ["body", "password"] for err in body["detail"])

    def test_rejects_empty_full_name_with_422(self, client: TestClient) -> None:
        bad = {**REGISTER_PAYLOAD, "full_name": ""}
        response = client.post("/auth/register", json=bad)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_rejects_role_field_to_prevent_privilege_escalation(self, client: TestClient) -> None:
        """Mass assignment protection.

        Even if a client includes 'role' in the body, the schema's
        extra='forbid' must reject the request rather than silently
        ignore the field. This is defense against privilege escalation.
        """
        hostile = {**REGISTER_PAYLOAD, "role": "admin"}
        response = client.post("/auth/register", json=hostile)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = response.json()
        assert any(
            err["type"] == "extra_forbidden" and err["loc"] == ["body", "role"]
            for err in body["detail"]
        )


# --------------------------------------------------------------------------- #
# POST /auth/login
# --------------------------------------------------------------------------- #
class TestLogin:
    """POST /auth/login"""

    def test_returns_access_token_on_valid_credentials(self, client: TestClient) -> None:
        client.post("/auth/register", json=REGISTER_PAYLOAD)
        response = client.post(
            "/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": REGISTER_PAYLOAD["password"],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0
        # JWT structure: three dot-separated base64 segments.
        assert body["access_token"].count(".") == 2

    def test_returns_401_with_generic_message_on_wrong_password(self, client: TestClient) -> None:
        client.post("/auth/register", json=REGISTER_PAYLOAD)
        response = client.post(
            "/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid email or password"

    def test_returns_401_with_same_message_on_unknown_email(self, client: TestClient) -> None:
        """User enumeration prevention.

        The response for an unknown email must be byte-identical to the
        response for a wrong password, so an attacker cannot probe which
        emails are registered.
        """
        response = client.post(
            "/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "AnyPassword123",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid email or password"

    def test_rejects_malformed_email_with_422(self, client: TestClient) -> None:
        response = client.post(
            "/auth/login",
            json={"email": "not-an-email", "password": "anything"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --------------------------------------------------------------------------- #
# GET /auth/me
# --------------------------------------------------------------------------- #
class TestMe:
    """GET /auth/me"""

    def test_returns_current_user_with_valid_token(
        self, authenticated_client: TestClient, test_user: User
    ) -> None:
        response = authenticated_client.get("/auth/me")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["id"] == test_user.id
        assert body["email"] == test_user.email
        assert body["full_name"] == test_user.full_name
        assert body["role"] == test_user.role.value
        assert "hashed_password" not in body

    def test_returns_401_without_token(self, client: TestClient) -> None:
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    def test_returns_401_with_malformed_token(self, client: TestClient) -> None:
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    def test_returns_401_with_expired_token(self, client: TestClient, test_user: User) -> None:
        expired_token = create_access_token(
            subject=test_user.id,
            expires_delta=timedelta(seconds=-1),
        )
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    def test_returns_401_when_token_references_nonexistent_user(self, client: TestClient) -> None:
        """A token signed for a user that no longer exists in the database
        must be rejected, even if the signature is valid.
        """
        ghost_token = create_access_token(subject=9999)
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {ghost_token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    def test_returns_specific_message_when_user_is_disabled(
        self,
        client: TestClient,
        test_user: User,
        db_session: Session,
    ) -> None:
        """When the user is deactivated, the token remains cryptographically
        valid but the dependency must reject it with a distinct message.
        This message is safe to expose because the attacker had to know a
        valid user to reach this branch.
        """
        # Deactivate the user directly in DB.
        test_user.is_active = False
        db_session.commit()

        # Use a fresh token (the user existed and was active when issued).
        token = create_access_token(subject=test_user.id)
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "User account is disabled"
