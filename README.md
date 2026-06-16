# VetClinic API

> Production-grade REST API for veterinary clinic management, built with FastAPI and PostgreSQL. Implements JWT authentication, soft-delete to preserve medical history, and an integration test suite that runs against a real PostgreSQL database in CI.

[![CI](https://github.com/JuanPablo-Aramburo-Dev/vetclinic-api/actions/workflows/ci.yml/badge.svg)](https://github.com/JuanPablo-Aramburo-Dev/vetclinic-api/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Highlights

- **JWT authentication with documented security properties.** Bearer tokens signed with HS256, bcrypt password hashing (12 rounds), and explicit mitigations for mass assignment and user enumeration attacks — all asserted by integration tests.
- **Integration tests against a real PostgreSQL database.** 54 tests covering happy paths, error cases, and security properties. No SQLite shortcuts; the test suite catches issues that mock-based tests miss (enum constraints, foreign key cascades, native types).
- **CI pipeline that applies migrations before tests.** GitHub Actions provisions a PostgreSQL service container, runs `alembic upgrade head`, and only then executes pytest. Broken migrations fail the PR, not the deployment.
- **Conventional Commits with atomic commits per architectural layer.** PRs land as ordered sequences: `feat(models) → feat(schemas) → feat(services) → feat(api) → test`. Each commit compiles, passes tests, and is independently reviewable.

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Web framework | FastAPI 0.118 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 16 |
| Migrations | Alembic 1.13 |
| Validation | Pydantic v2 |
| Auth | python-jose (JWT, HS256) + bcrypt 5.0 |
| Testing | pytest + TestClient (real PostgreSQL) |
| Linting / Formatting | Ruff |
| Containerization | Docker + docker-compose |
| CI | GitHub Actions |

## Architecture

The API follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│  HTTP Layer (app/api/)                                      │
│  Routers, request/response schemas, HTTP status mapping     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Service Layer (app/services/)                              │
│  Business logic, domain exceptions, no HTTP concerns        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Data Layer (app/models/, app/db/)                          │
│  SQLAlchemy models, sessions, Alembic migrations            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                  ┌────────▼────────┐
                  │   PostgreSQL    │
                  └─────────────────┘
```

Domain exceptions from the service layer are mapped to HTTP status codes at the router layer. The same exception can map to different codes depending on context — for example, `OwnerNotFoundError` becomes `422 Unprocessable Entity` when creating a pet with an invalid `owner_id` (the body references a missing resource), but `404 Not Found` when listing `/clients/{id}/pets/` (the URL points to a missing resource).


## Project Structure

```
app/
├── api/          # HTTP routers (auth, clients, pets) and shared dependencies
├── core/         # Configuration and cryptographic utilities
├── db/           # SQLAlchemy session, base class, and timestamp mixin
├── models/       # ORM models (User, Client, Pet)
├── schemas/      # Pydantic schemas (Base, Create, Update, Read patterns)
└── services/     # Business logic and domain exceptions

alembic/          # Database migrations
tests/            # Integration tests (run against real PostgreSQL)
.github/workflows/ # CI pipeline
```

## Quick Start

Requires Docker and Docker Compose installed locally.

```bash
# 1. Clone and enter the repo
git clone https://github.com/JuanPablo-Aramburo-Dev/vetclinic-api.git
cd vetclinic-api

# 2. Copy environment template and generate a SECRET_KEY
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD and generate SECRET_KEY with:
#   openssl rand -hex 32

# 3. Start PostgreSQL, apply migrations, run the API
docker compose up -d db
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive documentation (Swagger UI) is at `http://localhost:8000/docs`.

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Self-service user registration (always assigns `client` role) |
| POST | `/auth/login` | No | Exchange credentials for a JWT access token |
| GET | `/auth/me` | Yes | Return the authenticated user's identity |

### Clients

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/clients/` | Yes | List clients (paginated with `skip` and `limit`) |
| POST | `/clients/` | Yes | Create a new client |
| GET | `/clients/{id}` | Yes | Get a client by id |
| PATCH | `/clients/{id}` | Yes | Partially update a client |
| DELETE | `/clients/{id}` | Yes | Delete a client |

### Pets

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/pets/` | Yes | List active pets (use `?include_inactive=true` for soft-deleted) |
| POST | `/pets/` | Yes | Create a new pet (validates that the owner exists) |
| GET | `/pets/{id}` | Yes | Get a pet by id (returns regardless of active state) |
| PATCH | `/pets/{id}` | Yes | Partially update a pet (set `is_active: true` to reactivate) |
| DELETE | `/pets/{id}` | Yes | Soft-delete a pet (marks as inactive; idempotent) |
| GET | `/clients/{id}/pets/` | Yes | List pets belonging to a specific client |

### Health

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Liveness check |
| GET | `/` | No | API metadata |

Full request/response schemas are available in the auto-generated OpenAPI specification at `/docs` (Swagger UI) or `/openapi.json`.

## Security Properties

Each property below is asserted by an integration test in `tests/test_auth.py`. The README documents what the API does; the tests prove it.

### Password handling
- **Bcrypt with 12 rounds** for password hashing (`app/core/security.py`). Each hash includes a randomly generated salt, so hashing the same password twice produces different (but both valid) hashes.
- **Constant-time comparison** via `bcrypt.checkpw` prevents timing attacks during verification.
- **Hashed passwords never leave the database.** The `UserRead` Pydantic schema excludes `hashed_password` from every response.

### Token handling
- **JWT with HS256** (HMAC-SHA256). Tokens carry `sub` (user id as string per RFC 7519), `exp`, `iat`, and `type: "access"`.
- **Explicit type check on decode.** A token with a different `type` claim is rejected, anticipating future refresh tokens.
- **Tokens are not stored server-side.** Authentication is stateless; only the `SECRET_KEY` is required to verify a token.

### Mass assignment prevention
- **`UserRegister` schema uses `extra="forbid"`.** A request containing the `role` field is rejected with `422 Unprocessable Entity` before reaching the service layer. This prevents a public endpoint from being used to self-assign the `admin` role.
- **Defense in depth: the service hardcodes `UserRole.CLIENT`** for self-registration. Even if the schema were misconfigured, the role could not be elevated through this endpoint.

### User enumeration prevention
- **Identical 401 response** for "unknown email" and "wrong password" on `/auth/login`. An attacker cannot probe which emails are registered by comparing error messages.
- **Dummy bcrypt hash verification** runs when the user does not exist, so response times are not measurably different between the two cases. Prevents timing-based enumeration.

### Authentication enforcement
- **All `/clients/` and `/pets/` endpoints require a valid bearer token.** Missing or invalid tokens receive `401 Unauthorized` before any business logic runs.
- **Three distinct 401 messages** based on how far the token validation progressed: `"Not authenticated"` (no header), `"Could not validate credentials"` (malformed, expired, or tampered), `"User account is disabled"` (valid token but inactive user). The granularity is intentional and only exposed to clients that have already passed earlier validation steps.

## Testing

The test suite runs against a real PostgreSQL database (no SQLite, no mocks). This catches issues that mock-based tests miss: native enum types, foreign-key cascades, unique constraints, and Decimal precision.

### Run the tests locally

```bash
# 1. Ensure the database container is running
docker compose up -d db

# 2. Create the test database (one-time setup)
docker exec -it vetclinic_db psql -U vetclinic -d vetclinic_db \
    -c "CREATE DATABASE vetclinic_test_db;"
POSTGRES_DB=vetclinic_test_db alembic upgrade head

# 3. Run the suite
pytest -v
```

### Coverage by file

| File | Tests | Focus |
|---|---|---|
| `tests/test_health.py` | 5 | Liveness and metadata endpoints |
| `tests/test_auth.py` | 16 | Registration, login, JWT validation, security properties |
| `tests/test_clients.py` | 14 | Client CRUD + auth protection |
| `tests/test_pets.py` | 19 | Pet CRUD + soft delete + nested endpoint + auth protection |
| **Total** | **54** | Runs in ~8.5 seconds |

### Fixtures

- **`clean_database`** — `autouse` fixture that truncates all tables between tests, ensuring isolation without manual cleanup in each test.
- **`client`** — `TestClient` with `get_db` overridden to use the test database. Used for unauthenticated tests.
- **`authenticated_client`** — `TestClient` with a pre-applied `Authorization: Bearer <token>` header. Used for tests that hit protected endpoints.
- **`test_user`, `auth_headers`** — building blocks for the authenticated client; available separately for tests that need finer control (e.g., generating expired tokens).