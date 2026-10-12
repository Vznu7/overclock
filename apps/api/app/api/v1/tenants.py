from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db, set_session_tenant
from app.core.dependencies import get_current_user, log_audit_event, require_roles
from app.domains.audit.models import AuditAction
from app.domains.auth.models import User, UserRole
from app.domains.tenants.models import Tenant, TenantSettings
from app.domains.tenants.schemas import (
    TenantCreate,
    TenantRead,
    TenantSettingsRead,
    TenantSettingsUpdate,
)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post(
    "",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Tenant Mill",
)
def register_tenant(
    payload: TenantCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> Tenant:
    existing = db.query(Tenant).filter(Tenant.id == payload.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant '{payload.id}' already exists",
        )

    tenant = Tenant(
        id=payload.id,
        name=payload.name,
        cluster=payload.cluster,
        gstin=payload.gstin,
        currency=payload.currency,
        timezone=payload.timezone,
        is_active=True,
    )
    db.add(tenant)
    db.flush()

    # Set tenant context for RLS-protected TenantSettings insertion
    set_session_tenant(db, tenant.id)

    # Create default settings
    settings = TenantSettings(
        tenant_id=tenant.id,
        sewing_capacity_daily=1500,
        working_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        risk_thresholds={
            "r1_need_by_days": 7,
            "r2_gate_days": 7,
            "r3_deficit_multiplier": 1.25,
            "r4_jobwork_tolerance_percent": 2.0,
            "r5_gate_overdue_days": 0,
            "r6_missing_input_lead_days": 14,
        },
        monthly_ai_budget_inr=500.00,
        daily_ai_budget_cap_inr=50.00,
    )
    db.add(settings)
    db.flush()

    log_audit_event(
        db=db,
        tenant_id=tenant.id,
        entity_type="tenant",
        entity_id=tenant.id,
        action=AuditAction.CREATE,
        changes={"name": tenant.name, "cluster": tenant.cluster},
        request=request,
    )
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/current", response_model=TenantRead, summary="Get Current Tenant & Settings")
def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return tenant


@router.patch(
    "/current/settings",
    response_model=TenantSettingsRead,
    summary="Update Mill Settings & Risk Tolerances",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER))],
)
def update_tenant_settings(
    payload: TenantSettingsUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantSettings:
    set_session_tenant(db, current_user.tenant_id)
    settings = (
        db.query(TenantSettings).filter(TenantSettings.tenant_id == current_user.tenant_id).first()
    )
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant settings not found",
        )

    changes: dict = {}
    if payload.sewing_capacity_daily is not None:
        changes["sewing_capacity_daily"] = payload.sewing_capacity_daily
        settings.sewing_capacity_daily = payload.sewing_capacity_daily
    if payload.working_days is not None:
        changes["working_days"] = payload.working_days
        settings.working_days = payload.working_days
    if payload.risk_thresholds is not None:
        changes["risk_thresholds"] = payload.risk_thresholds
        settings.risk_thresholds = payload.risk_thresholds
    if payload.monthly_ai_budget_inr is not None:
        changes["monthly_ai_budget_inr"] = payload.monthly_ai_budget_inr
        settings.monthly_ai_budget_inr = payload.monthly_ai_budget_inr
    if payload.daily_ai_budget_cap_inr is not None:
        changes["daily_ai_budget_cap_inr"] = payload.daily_ai_budget_cap_inr
        settings.daily_ai_budget_cap_inr = payload.daily_ai_budget_cap_inr

    if changes:
        log_audit_event(
            db=db,
            tenant_id=current_user.tenant_id,
            entity_type="tenant_settings",
            entity_id=current_user.tenant_id,
            action=AuditAction.UPDATE,
            user_id=current_user.id,
            changes=changes,
            request=request,
        )
        db.commit()
        db.refresh(settings)

    return settings
