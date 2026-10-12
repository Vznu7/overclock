from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import check_db_connection

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health/live", summary="Liveness Probe")
@router.get("/healthz", summary="Render/K8s Liveness Probe")
def liveness() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready", summary="Readiness Probe")
def readiness() -> JSONResponse:
    db_ok = check_db_connection()
    all_ready = db_ok

    status_code = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ready else "degraded",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "dependencies": {
                "database": "connected" if db_ok else "unreachable",
                "storage": "ready",
                "ai_provider": settings.LLM_PROVIDER,
            },
            "timestamp_utc": datetime.now(UTC).isoformat(),
        },
    )
