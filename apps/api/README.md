# OVERCLOCK API

FastAPI backend service for OVERCLOCK — Multi-tenant AI SaaS for Indian Garment Manufacturers.

## Running Locally

```bash
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload
```

## Running Tests

```bash
uv run pytest --cov=app tests/
```
