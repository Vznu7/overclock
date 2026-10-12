import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.risk.schemas import OrderRiskSummary
from app.domains.risk.services import RiskControlService

router = APIRouter(tags=["Unified Risk Control Tower (R1-R6)"])


@router.get(
    "/risk/evaluate",
    response_model=list[OrderRiskSummary],
    summary="Comprehensive deterministic evaluation across Rules R1 to R6 for all active orders",
)
def evaluate_all_risks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrderRiskSummary]:
    return RiskControlService.evaluate_all_risks(db, current_user.tenant_id)


@router.get(
    "/risk/orders/{order_id}",
    response_model=OrderRiskSummary,
    summary="Evaluate full deterministic risk matrix for a single order",
)
def evaluate_order_risk(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderRiskSummary:
    try:
        return RiskControlService.evaluate_order_risk(db, current_user.tenant_id, order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
