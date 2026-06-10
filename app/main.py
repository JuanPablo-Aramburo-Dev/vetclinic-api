"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api import auth, clients, pets
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="REST API for veterinary clinic management",
    version="0.1.0",
    debug=settings.debug,
)

# Routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(pets.router)
app.include_router(pets.clients_pets_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Liveness probe endpoint.

    Used by load balancers, monitors, and orchestrators to check if
    the service is up.
    """
    return {"status": "ok", "service": settings.app_name}


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    """Root endpoint with API metadata."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }
