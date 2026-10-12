import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.domains.auth.models import User, UserRole
from app.domains.production.schemas import (
    DailyProductionLogCreate,
    DailyProductionLogResponse,
    OrderProductionSummary,
    ProductionLineCreate,
    ProductionLineResponse,
)
from app.domains.production.services import ProductionService
from app.domains.risk.schemas import RiskAssessment

router = APIRouter(tags=["Production Floor & Pacing Risk"])


@router.get(
    "/production/lines",
    response_model=list[ProductionLineResponse],
    summary="List all factory production lines",
)
def list_production_lines(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProductionLineResponse]:
    return ProductionService.list_lines(db, current_user.tenant_id)


@router.post(
    "/production/lines",
    response_model=ProductionLineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new production line",
)
def create_production_line(
    data: ProductionLineCreate,
    current_user: User = Depends(
        require_roles(UserRole.OWNER, UserRole.PRODUCTION_MANAGER)
    ),
    db: Session = Depends(get_db),
) -> ProductionLineResponse:
    try:
        return ProductionService.create_line(db, current_user.tenant_id, data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create line: {str(e)}",
        ) from e


@router.get(
    "/production/logs",
    response_model=list[DailyProductionLogResponse],
    summary="List daily production logs with filters",
)
def list_daily_production_logs(
    order_id: uuid.UUID | None = None,
    line_id: uuid.UUID | None = None,
    stage: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DailyProductionLogResponse]:
    return ProductionService.list_daily_logs(
        db,
        current_user.tenant_id,
        order_id=order_id,
        line_id=line_id,
        stage=stage,
        limit=limit,
    )


@router.post(
    "/production/logs",
    response_model=DailyProductionLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log daily floor output (30-second mobile entry)",
)
def record_daily_production_log(
    data: DailyProductionLogCreate,
    current_user: User = Depends(
        require_roles(UserRole.SUPERVISOR, UserRole.PRODUCTION_MANAGER, UserRole.OWNER)
    ),
    db: Session = Depends(get_db),
) -> DailyProductionLogResponse:
    try:
        return ProductionService.record_daily_log(
            db,
            current_user.tenant_id,
            current_user.id,
            data,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record production log: {str(e)}",
        ) from e


@router.get(
    "/production/orders/{order_id}/summary",
    response_model=OrderProductionSummary,
    summary="Get cumulative production pacing and completion forecast for an order",
)
def get_order_production_summary(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderProductionSummary:
    try:
        return ProductionService.get_order_production_summary(
            db, current_user.tenant_id, order_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "/risk/production",
    response_model=list[RiskAssessment],
    summary="Evaluate Rule R3 (Sewing Run-Rate Slippage) for all active orders",
)
def evaluate_production_risks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RiskAssessment]:
    return ProductionService.evaluate_all_production_risks(db, current_user.tenant_id)
