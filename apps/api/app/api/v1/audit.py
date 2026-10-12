from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.domains.audit.models import AuditLog
from app.domains.audit.schemas import AuditLogRead
from app.domains.auth.models import User, UserRole

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=list[AuditLogRead],
    summary="List Tenant Audit Logs (Append-Only)",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.VIEWER))],
)
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    entity_type: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    query = (
        db.query(AuditLog)
        .filter(AuditLog.tenant_id == current_user.tenant_id)
        .order_by(AuditLog.created_at.desc())
    )
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    return query.limit(limit).all()
