import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, log_audit_event, require_roles
from app.core.security import get_password_hash
from app.domains.audit.models import AuditAction
from app.domains.auth.models import User, UserRole
from app.domains.auth.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserRead],
    summary="List Tenant Users",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER))],
)
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    return (
        db.query(User)
        .filter(User.tenant_id == current_user.tenant_id)
        .order_by(User.created_at.desc())
        .all()
    )


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create New User in Tenant",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    # Check duplicate email in this tenant
    existing = (
        db.query(User)
        .filter(User.tenant_id == current_user.tenant_id, User.email == payload.email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{payload.email}' already exists in this tenant",
        )

    new_user = User(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=payload.role.value,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="user",
        entity_id=str(new_user.id),
        action=AuditAction.CREATE,
        user_id=current_user.id,
        changes={"email": new_user.email, "role": new_user.role, "name": new_user.full_name},
        request=request,
    )
    db.commit()
    db.refresh(new_user)
    return new_user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update Tenant User Role / Status",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    target_user = (
        db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    )
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    changes: dict[str, str | bool] = {}
    if payload.full_name is not None and payload.full_name != target_user.full_name:
        changes["full_name"] = payload.full_name
        target_user.full_name = payload.full_name
    if payload.role is not None and payload.role.value != target_user.role:
        changes["role"] = payload.role.value
        target_user.role = payload.role.value
    if payload.is_active is not None and payload.is_active != target_user.is_active:
        changes["is_active"] = payload.is_active
        target_user.is_active = payload.is_active

    if changes:
        log_audit_event(
            db=db,
            tenant_id=current_user.tenant_id,
            entity_type="user",
            entity_id=str(target_user.id),
            action=AuditAction.UPDATE,
            user_id=current_user.id,
            changes=changes,
            request=request,
        )
        db.commit()
        db.refresh(target_user)

    return target_user
