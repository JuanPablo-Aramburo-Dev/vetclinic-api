"""Pytest configuration and shared fixtures.

This module sets up:
- A separate test database connection (independent from dev DB).
- A db_session fixture that provides a clean session per test.
- A client fixture that overrides FastAPI's get_db dependency to
  use the test database.
- Authentication fixtures (test_user, auth_headers, authenticated_client)
  for tests that hit protected endpoints.
- Automatic table truncation between tests for isolation.
"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Force test database BEFORE importing the app, so Settings picks it up.
os.environ.setdefault("POSTGRES_DB", "vetclinic_test_db")

# Build the test engine using the same config as the app.
# The POSTGRES_DB override above ensures we connect to the test DB.
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole

settings = get_settings()
test_engine = create_engine(settings.database_url, pool_pre_ping=True)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def _truncate_all_tables(engine) -> None:
    """Truncate all data tables, restarting identity sequences.

    alembic_version is left untouched so the schema is preserved.
    """
    with engine.begin() as conn:
        # CASCADE handles tables with foreign keys to each other.
        conn.execute(text("TRUNCATE TABLE pets, clients, users RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    """Truncate all tables before each test for isolation.

    autouse=True applies this to every test automatically; no need
    to declare it as a parameter.
    """
    _truncate_all_tables(test_engine)
    yield
    # No teardown needed; next test will truncate again.


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a database session connected to the test DB."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _override_get_db() -> Generator[Session, None, None]:
    """Replacement for app.db.session.get_db that uses the test DB."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient with get_db overridden to the test DB.

    Use this for tests that hit unprotected endpoints (/health, /,
    /auth/register, /auth/login) or tests that verify auth failures
    (e.g., missing token returns 401).
    """
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# Authentication fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create and return a test user (admin role, active).

    Inserted directly into the database (not via /auth/register) so the
    fixture is independent of the registration endpoint. Role is ADMIN
    so the user can hit any protected endpoint regardless of future
    role-based authorization rules.
    """
    user = User(
        email="testuser@example.com",
        full_name="Test User",
        hashed_password=hash_password("TestPassword123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Return Authorization headers carrying a valid JWT for test_user."""
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def authenticated_client(
    client: TestClient,
    auth_headers: dict[str, str],
) -> TestClient:
    """TestClient with the Authorization header pre-applied to every request.

    Use this for tests of protected endpoints. The underlying client
    fixture already overrides get_db to point to the test database.
    """
    client.headers.update(auth_headers)
    return client
