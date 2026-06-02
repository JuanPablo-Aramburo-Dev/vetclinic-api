# VetClinic API

REST API for veterinary clinic management. Manages clients, pets, veterinarians, appointments, medical records, and vaccinations.

## Status

🚧 Work in progress. Currently implementing core infrastructure.

## Tech Stack

- **Language:** Python 3.13
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Auth:** JWT
- **Tests:** pytest
- **Containerization:** Docker + docker-compose

## Local Development

### Requirements

- Python 3.13+
- Docker Desktop (for the next phase)

### Setup

```bash
git clone https://github.com/JuanPablo-Aramburo-Dev/vetclinic-api.git
cd vetclinic-api
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Then open:

- `http://localhost:8000/docs` — interactive API documentation
- `http://localhost:8000/health` — health check

## Project Structure
app/
├── api/         # endpoint routers (coming soon)
├── core/        # configuration and security
├── db/          # database session (coming soon)
├── models/      # SQLAlchemy models (coming soon)
├── schemas/     # Pydantic schemas (coming soon)
└── services/    # business logic (coming soon)
tests/           # pytest tests

## Roadmap

- [x] FastAPI scaffold with config
- [ ] Docker + PostgreSQL setup
- [ ] CI/CD with GitHub Actions
- [ ] SQLAlchemy models and Alembic migrations
- [ ] Authentication and authorization (JWT, roles)
- [ ] Clients and pets CRUD
- [ ] Appointments with conflict detection
- [ ] Medical records and vaccines
- [ ] Reports
- [ ] Production deployment

## License

MIT
