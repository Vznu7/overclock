from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.jobwork import router as jobwork_router
from app.api.v1.materials import router as materials_router
from app.api.v1.orders import router as orders_router
from app.api.v1.production import router as production_router
from app.api.v1.risk import router as risk_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.users import router as users_router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "Starting %s v%s [%s mode]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant AI SaaS for Garment Manufacturers in India",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount health routes at root level for orchestrators & docker checks
app.include_router(health_router)

# Mount all v1 routers under /api/v1
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(materials_router, prefix="/api/v1")
app.include_router(production_router, prefix="/api/v1")
app.include_router(jobwork_router, prefix="/api/v1")
app.include_router(risk_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
        "status": "online",
    }
