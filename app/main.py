"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api import clients
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="REST API for veterinary clinic management",
    version="0.1.0",
)

# Routers
app.include_router(clients.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": f"Welcome to {settings.app_name}"}