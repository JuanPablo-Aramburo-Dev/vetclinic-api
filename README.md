# VetClinic API

> Production-grade REST API for veterinary clinic management, built with FastAPI and PostgreSQL. Implements JWT authentication, soft-delete to preserve medical history, and an integration test suite that runs against a real PostgreSQL database in CI.

[![CI](https://github.com/JuanPablo-Aramburo-Dev/vetclinic-api/actions/workflows/ci.yml/badge.svg)](https://github.com/JuanPablo-Aramburo-Dev/vetclinic-api/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Live API](https://img.shields.io/badge/Live%20API-35.87.203.193-success.svg)](http://35.87.203.193/docs)

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

## Deployment

The API is deployed on AWS using a custom VPC, with the database isolated in a private subnet.

**Live API:** `http://35.87.203.193` ([Swagger UI](http://35.87.203.193/docs))

> Currently served over HTTP. The architecture is already prepared for HTTPS via ACM and nginx — TLS will be enabled once a custom domain is acquired (ACM requires domain ownership for certificate validation).

### Infrastructure

```
                         Internet
                            │
                            │ :80
                            ▼
                  ┌───────────────────┐
                  │  Internet Gateway  │
                  └─────────┬─────────┘
                            │
┌───────────────────────────┼────────────────────────────────┐
│                  VPC (10.0.0.0/16)                          │
│                            │                                │
│              ┌─────────────▼─────────────┐                  │
│              │      Public Subnet         │                  │
│              │      EC2 t3.micro          │                  │
│              │  ┌───────────────────────┐  │                  │
│              │  │ nginx (:80 → :8000)   │  │                  │
│              │  └───────────┬───────────┘  │                  │
│              │  ┌───────────▼───────────┐  │                  │
│              │  │ Docker container       │  │                  │
│              │  │ FastAPI + uvicorn      │  │                  │
│              │  └───────────────────────┘  │                  │
│              │  IAM Role: Secrets Manager  │                  │
│              └─────────────┬─────────────┘                  │
│                            │ :5432                           │
│                            │ (SG-to-SG only)                 │
│              ┌─────────────▼─────────────┐                  │
│              │     Private Subnets        │                  │
│              │     RDS db.t3.micro         │                  │
│              │     PostgreSQL 16           │                  │
│              │     No public IP            │                  │
│              └─────────────────────────────┘                  │
└────────────────────────────────────────────────────────────────┘
```

### Security model

- **RDS has no public IP.** Database access is restricted to traffic from the EC2 Security Group on port 5432 — not from any CIDR range.
- **EC2 accepts SSH only from a single IP** (the maintainer's), and HTTP/HTTPS from the internet.
- **No long-lived AWS credentials on the instance.** EC2 uses an IAM Role (`vetclinic-ec2-role`) to access AWS Secrets Manager — no Access Keys are stored on the server.
- **Database credentials live in AWS Secrets Manager**, not in environment files committed to git or baked into the Docker image.
- **Root AWS account is not used for operations.** All infrastructure is managed through a dedicated IAM user with MFA enabled.

### Deployed stack

| Component | Choice | Reasoning |
|---|---|---|
| Compute | EC2 t3.micro | Free Tier eligible; sufficient for portfolio-scale traffic |
| Database | RDS PostgreSQL 16, db.t3.micro | Managed backups and patching; isolated in a private subnet |
| Reverse proxy | nginx | Decouples the public-facing port from uvicorn; required for the planned TLS termination |
| Container runtime | Docker + Docker Compose | Matches local development environment; single build artifact for both |
| Secrets | AWS Secrets Manager | Avoids plaintext credentials in `.env` files on the server |
| Excluded by design | ALB, NAT Gateway, ECS/Fargate, CloudFront | Each adds recurring cost not justified at this traffic scale; documented here so the omission reads as a decision, not an oversight |

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

## Design Decisions

A few decisions in this codebase have non-obvious reasoning. Documenting them here avoids the same questions in code review.

### Why bcrypt directly instead of passlib

`passlib 1.7.4` (the latest release) is incompatible with `bcrypt >= 4.1` because it reads `bcrypt.__about__.__version__`, an attribute removed in modern bcrypt. The mismatch manifests as a runtime error during the first password hash. After encountering this, I switched to using the `bcrypt` library directly. The API surface is small (`hashpw`, `checkpw`, `gensalt`), and it's the library that's actually maintained.

### Why JSON for `/auth/login` instead of `OAuth2PasswordRequestForm`

FastAPI tutorials typically use `OAuth2PasswordRequestForm`, which accepts `application/x-www-form-urlencoded` and names the credentials field `username`. I use JSON instead, with the field named `email`. The reasoning is consistency: the rest of the API is JSON-only, and the field name reflects the actual data. The cost of diverging from the FastAPI tutorial pattern is small; the benefit is a uniform contract across endpoints.

### Why access-only tokens (no refresh tokens)

A complete implementation would use short-lived access tokens (15 min) plus longer-lived refresh tokens (7-30 days) with rotation and a revocation store. That requires either a Redis instance or a dedicated database table for refresh tokens, plus token rotation logic and a `/auth/refresh` endpoint. For the scope of this portfolio, the added complexity isn't justified. Access tokens expire after 60 minutes, which is a defensible default. Refresh tokens are documented as a next step.

### Why soft delete instead of hard delete for pets

Veterinary records carry medical history (vaccines, conditions, prior treatments). Hard-deleting a pet because a client no longer brings it in destroys data that may be needed for clinical decisions when the client returns or transfers records to another clinic. The `is_active` flag hides the pet from operational listings (the default `GET /pets/`) but preserves the row and its relationships. Reactivation is a single `PATCH` setting `is_active: true`.

### Why integration tests against real PostgreSQL instead of SQLite or mocks

SQLite does not support PostgreSQL's native enum types, `NUMERIC(precision, scale)` semantics, or `ON DELETE CASCADE` behavior in the same way. Mocks of the database session don't catch the same class of bugs at all. Running 54 tests against a real PostgreSQL instance takes about 8.5 seconds — fast enough that the cost is negligible, and the tests catch real issues (enum mismatches, foreign-key violations, decimal precision) before they reach CI or production.

### Why different HTTP status codes for the same domain exception

`OwnerNotFoundError` maps to `422 Unprocessable Entity` when raised from `POST /pets/` (the request body references a missing resource — syntactically valid but semantically incorrect) and to `404 Not Found` when raised from `GET /clients/{id}/pets/` (the URL path itself points to a missing resource). The service layer raises one exception; the router decides the HTTP code based on context. This keeps domain logic transport-agnostic and lets the same business rule be reused in non-HTTP contexts (e.g., a future CLI or background job) without leaking HTTP concerns.

## What's Next

These items are deliberately out of scope for the current iteration. Each is listed with the reason for deferral and a sketch of the approach.

- **Refresh tokens with rotation.** Requires a server-side store for issued refresh tokens (Redis or a dedicated table) and a `/auth/refresh` endpoint with token rotation. Pairs naturally with a token revocation list for immediate logout.
- **Role-based authorization.** The `User` model already carries `admin`, `vet`, and `client` roles. Endpoints currently enforce only "authenticated", not "authorized for this resource". The next step is a `require_role(*allowed)` dependency factory and resource-level ownership checks (e.g., a client can only see their own pets).
- **Remaining domain resources.** Veterinarians, Appointments, Medical Records, and Vaccines are modeled in the ERD but not yet implemented as endpoints. They follow the same layered pattern as Clients and Pets.
- **Rate limiting.** `/auth/login` is the most obvious candidate (brute-force protection). FastAPI's middleware ecosystem includes `slowapi`, which works with Redis or an in-memory store.
- **HTTPS via ACM.** The application is deployed and reachable over HTTP. The nginx reverse-proxy layer is already in place specifically to support TLS termination; enabling it is a matter of acquiring a domain and requesting an ACM certificate — no architectural changes required.
- **Structured logging and observability.** Currently no logging is emitted beyond uvicorn's default. Adding `structlog` with JSON output and integrating with CloudWatch or a similar aggregator is the natural next step before production traffic.

## License

This project is released under the [MIT License](LICENSE).
