FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /bin/uv

# Copy project files needed for package installation
COPY pyproject.toml README.md uv.lock* /app/
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Install dependencies using uv
RUN uv pip install --system -e .

# Expose port (default 8000)
EXPOSE 8000

# Health check against health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/healthz || exit 1

# Launch uvicorn listening on Render's dynamic PORT or default 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
