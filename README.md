# OVERCLOCK

> Multi-tenant AI SaaS for Indian Garment Manufacturers (Knitwear & Woven Exporters)

## Quickstart

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ & npm
- Python 3.12+ & `uv`

### 1. Configure Environment
```bash
cp .env.example .env
```

### 2. Boot Local Services (Docker Compose)
```bash
make up
# or
docker compose -f infra/docker-compose.yml up -d
```
Services available:
- **Web App**: http://localhost:5173
- **FastAPI**: http://localhost:8000 (Swagger docs: http://localhost:8000/docs)
- **MinIO Console**: http://localhost:9001 (User: `minioadmin`, Pass: `minioadmin`)
- **PostgreSQL**: `localhost:5432`

### 3. Run Tests & Linters
```bash
make test
make lint
```

### 4. Seed Fictional Demo Tenant
```bash
make seed
```
