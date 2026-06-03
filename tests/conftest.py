"""Shared pytest fixtures for the test suite."""

import os

import pytest
from fastapi.testclient import TestClient

# Set required environment variables before importing app
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://test:test@localhost:5432/test_db",
)


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provide a TestClient instance for the FastAPI app.

    Scope='session' means the same client is reused for all tests in the
    test session, which is faster than creating one per test.
    """
    # Import here so env vars are set before app reads them
    from app.main import app

    return TestClient(app)
