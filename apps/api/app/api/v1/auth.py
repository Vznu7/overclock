from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db, set_session_tenant
from app.core.dependencies import get_current_user, log_audit_event
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.domains.audit.models import AuditAction
from app.domains.auth.models import User
from app.domains.auth.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserRead,
)
from app.domains.tenants.models import Tenant

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


@router.post(
    "/login", response_model=TokenResponse, summary="Argon2id Authentication & Token Issuance"
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    # 1. Set transaction context for RLS
    set_session_tenant(db, payload.tenant_id)

    # 2. Verify Tenant
    tenant = (
        db.query(Tenant).filter(Tenant.id == payload.tenant_id, Tenant.is_active.is_(True)).first()
    )
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant identifier or tenant inactive",
        )

    # 3. Find User
    user = (
        db.query(User)
        .filter(User.tenant_id == payload.tenant_id, User.email == payload.email)
        .first()
    )

    now = datetime.now(UTC)

    if not user:
        # Prevent timing enumeration
        verify_password(
            payload.password, "$argon2id$v=19$m=65536,t=3,p=4$fakefakefake$fakefakefake"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # 4. Check Lockout
    if user.locked_until and user.locked_until > now:
        remaining_minutes = max(1, int((user.locked_until - now).total_seconds() / 60))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked due to consecutive failed logins. Try again in {remaining_minutes} minutes.",
        )

    # 5. Verify Password
    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)

        log_audit_event(
            db=db,
            tenant_id=payload.tenant_id,
            entity_type="user",
            entity_id=str(user.id),
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id,
            changes={"attempt": user.failed_login_attempts, "locked": bool(user.locked_until)},
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # 6. Success: Reset failed attempts & set last login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    user_id = user.id
    user_tenant_id = user.tenant_id
    user_role = user.role
    user_email = user.email
    user_full_name = user.full_name

    log_audit_event(
        db=db,
        tenant_id=payload.tenant_id,
        entity_type="user",
        entity_id=str(user_id),
        action=AuditAction.LOGIN_SUCCESS,
        user_id=user_id,
        request=request,
    )
    db.commit()

    # 7. Generate Tokens
    access_token = create_access_token(
        subject=str(user_id),
        tenant_id=user_tenant_id,
        role=user_role,
        extra_claims={"email": user_email, "full_name": user_full_name},
    )
    refresh_token = create_refresh_token(subject=str(user_id), tenant_id=user_tenant_id)

    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user_id,
        email=user_email,
        full_name=user_full_name,
        role=user_role,  # type: ignore[arg-type]
        tenant_id=user_tenant_id,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Access Token")
def refresh_token_endpoint(
    payload: RefreshTokenRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        claims = decode_token(payload.refresh_token)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from err

    if claims.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    tenant_id = claims.get("tenant_id")
    user_id = claims.get("sub")

    set_session_tenant(db, tenant_id)
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or valid",
        )

    new_access_token = create_access_token(
        subject=str(user.id),
        tenant_id=user.tenant_id,
        role=user.role,
        extra_claims={"email": user.email, "full_name": user.full_name},
    )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=payload.refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,  # type: ignore[arg-type]
        tenant_id=user.tenant_id,
    )


@router.get("/me", response_model=UserRead, summary="Get Current Authenticated User")
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout", summary="Logout & Invalidate Session")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}
