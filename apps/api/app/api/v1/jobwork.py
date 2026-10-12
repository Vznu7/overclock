import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.domains.auth.models import User, UserRole
from app.domains.jobwork.schemas import (
    JobworkChallanCreate,
    JobworkChallanReceive,
    JobworkChallanResponse,
    JobworkProcessorCreate,
    JobworkProcessorResponse,
)
from app.domains.jobwork.services import JobworkService
from app.domains.risk.schemas import RiskAssessment

router = APIRouter(tags=["Job-Work Hub & Process Anomaly Risk"])


@router.get(
    "/jobwork/processors",
    response_model=list[JobworkProcessorResponse],
    summary="List all job-work processors / finishing units",
)
def list_processors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobworkProcessorResponse]:
    return JobworkService.list_processors(db, current_user.tenant_id)


@router.post(
    "/jobwork/processors",
    response_model=JobworkProcessorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new job-work vendor",
)
def create_processor(
    data: JobworkProcessorCreate,
    current_user: User = Depends(
        require_roles(UserRole.OWNER, UserRole.MERCHANDISER, UserRole.PRODUCTION_MANAGER)
    ),
    db: Session = Depends(get_db),
) -> JobworkProcessorResponse:
    try:
        return JobworkService.create_processor(db, current_user.tenant_id, data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create processor: {str(e)}",
        ) from e


@router.get(
    "/jobwork/challans",
    response_model=list[JobworkChallanResponse],
    summary="List job-work delivery challans",
)
def list_challans(
    order_id: uuid.UUID | None = None,
    processor_id: uuid.UUID | None = None,
    challan_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobworkChallanResponse]:
    return JobworkService.list_challans(
        db,
        current_user.tenant_id,
        order_id=order_id,
        processor_id=processor_id,
        status=challan_status,
        limit=limit,
    )


@router.post(
    "/jobwork/challans",
    response_model=JobworkChallanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue outward delivery challan to processor",
)
def issue_challan(
    data: JobworkChallanCreate,
    current_user: User = Depends(
        require_roles(
            UserRole.OWNER,
            UserRole.MERCHANDISER,
            UserRole.PRODUCTION_MANAGER,
            UserRole.STORE_KEEPER,
        )
    ),
    db: Session = Depends(get_db),
) -> JobworkChallanResponse:
    try:
        return JobworkService.issue_challan(
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
            detail=f"Failed to issue challan: {str(e)}",
        ) from e


@router.post(
    "/jobwork/challans/{challan_id}/receive",
    response_model=JobworkChallanResponse,
    summary="Record inward receipt of processed goods with weight loss reconciliation",
)
def receive_challan(
    challan_id: uuid.UUID,
    data: JobworkChallanReceive,
    current_user: User = Depends(
        require_roles(
            UserRole.OWNER,
            UserRole.MERCHANDISER,
            UserRole.PRODUCTION_MANAGER,
            UserRole.STORE_KEEPER,
        )
    ),
    db: Session = Depends(get_db),
) -> JobworkChallanResponse:
    try:
        return JobworkService.receive_challan(
            db,
            current_user.tenant_id,
            current_user.id,
            challan_id,
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
            detail=f"Failed to receive challan: {str(e)}",
        ) from e


@router.get(
    "/risk/jobwork",
    response_model=list[RiskAssessment],
    summary="Evaluate Rule R4 (Job-Work Delay & Process Weight Loss Anomaly) for all active orders",
)
def evaluate_jobwork_risks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RiskAssessment]:
    return JobworkService.evaluate_all_jobwork_risks(db, current_user.tenant_id)


@router.get(
    "/risk/jobwork/{order_id}",
    response_model=RiskAssessment,
    summary="Evaluate Rule R4 for a specific order",
)
def evaluate_order_jobwork_risk(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RiskAssessment:
    try:
        return JobworkService.evaluate_order_jobwork_risk(
            db, current_user.tenant_id, order_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
