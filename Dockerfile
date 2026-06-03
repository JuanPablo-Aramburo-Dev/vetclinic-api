# syntax=docker/dockerfile:1.7

# ============================================================
# Stage 1: Builder - installs dependencies
# ============================================================
FROM python:3.13-slim AS builder

# Prevent Python from writing .pyc files and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements (cached layer if requirements don't change)
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# ============================================================
# Stage 2: Runtime - minimal final image
# ============================================================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

# Install runtime system deps (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY ./app ./app

# Expose port (informational, doesn't actually publish)
EXPOSE 8000

# Run uvicorn (production-grade)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
