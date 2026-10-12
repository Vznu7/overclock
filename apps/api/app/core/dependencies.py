import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db, set_session_tenant
from app.core.security import decode_token
from app.domains.audit.models import AuditAction, AuditLog
from app.domains.auth.models import User, UserRole


def get_current_user(
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT token, set database transaction tenant_id for RLS, and return active User."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_id: str | None = payload.get("tenant_id")
    user_id_str: str | None = payload.get("sub")

    if not tenant_id or not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user subject in token",
        ) from err

    # CRITICAL: Bind transaction to tenant for PostgreSQL Row-Level Security
    set_session_tenant(db, tenant_id)

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inaccessible under active tenant context",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    if user.locked_until and user.locked_until > datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked due to consecutive failed login attempts",
        )

    return user


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    """FastAPI dependency to enforce RBAC permissions."""
    allowed_values = {role.value for role in allowed_roles}

    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' lacks permission for this action. Allowed: {sorted(allowed_values)}",
            )
        return current_user

    return role_dependency


def log_audit_event(
    db: Session,
    tenant_id: str,
    entity_type: str,
    entity_id: str,
    action: AuditAction | str,
    user_id: uuid.UUID | None = None,
    changes: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    """Record an append-only audit log entry."""
    ip_addr = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    # Ensure transaction tenant matches
    set_session_tenant(db, tenant_id)

    log_entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action.value if isinstance(action, AuditAction) else str(action),
        changes_json=changes,
        ip_address=ip_addr,
        user_agent=user_agent,
    )
    db.add(log_entry)
    db.flush()
    return log_entry
