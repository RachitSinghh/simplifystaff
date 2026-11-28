import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import SESSION_ENDED_MESSAGE, get_db
from app.core.security import create_access_token, hash_secret
from app.models import Employee, OtpCode, RefreshToken
from app.schemas.auth import (
    LogoutIn,
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    OtpVerifyOut,
    RefreshIn,
    RefreshOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_EXPIRE_MINUTES = 5
INACTIVE_ACCOUNT_MESSAGE = "This account is no longer active. Contact your manager."
INVALID_CODE_MESSAGE = "That code doesn't match. Check the code and try again."


@router.post("/otp/request", response_model=OtpRequestOut)
def request_otp(payload: OtpRequestIn, db: Session = Depends(get_db)) -> OtpRequestOut:
    settings = get_settings()
    employee = db.scalars(select(Employee).where(Employee.phone == payload.phone)).first()

    if employee is not None and not employee.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, INACTIVE_ACCOUNT_MESSAGE)

    code = None
    if employee is not None:
        code = f"{secrets.randbelow(1_000_000):06d}"
        db.add(
            OtpCode(
                company_id=employee.company_id,
                employee_id=employee.id,
                code_hash=hash_secret(code),
                expires_at=datetime.now(UTC) + timedelta(minutes=OTP_EXPIRE_MINUTES),
            )
        )
        db.commit()

    return OtpRequestOut(
        message="If this phone number is registered, a verification code has been sent.",
        code=code if settings.otp_simulation_mode else None,
    )


@router.post("/otp/verify", response_model=OtpVerifyOut)
def verify_otp(payload: OtpVerifyIn, db: Session = Depends(get_db)) -> OtpVerifyOut:
    settings = get_settings()
    employee = db.scalars(select(Employee).where(Employee.phone == payload.phone)).first()

    otp = None
    if employee is not None:
        otp = db.scalars(
            select(OtpCode)
            .where(
                OtpCode.employee_id == employee.id,
                OtpCode.code_hash == hash_secret(payload.code),
            )
            .order_by(OtpCode.created_at.desc())
        ).first()

    now = datetime.now(UTC)
    if (
        employee is None
        or not employee.is_active
        or otp is None
        or otp.consumed_at is not None
        or otp.expires_at < now
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_CODE_MESSAGE)

    otp.consumed_at = now

    refresh_token_value = secrets.token_urlsafe(32)
    db.add(
        RefreshToken(
            company_id=employee.company_id,
            employee_id=employee.id,
            token_hash=hash_secret(refresh_token_value),
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()

    return OtpVerifyOut(
        access_token=create_access_token(str(employee.id)),
        refresh_token=refresh_token_value,
    )


@router.post("/refresh", response_model=RefreshOut)
def refresh_access_token(payload: RefreshIn, db: Session = Depends(get_db)) -> RefreshOut:
    token = db.scalars(
        select(RefreshToken).where(RefreshToken.token_hash == hash_secret(payload.refresh_token))
    ).first()

    now = datetime.now(UTC)
    if token is None or token.revoked_at is not None or token.expires_at < now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, SESSION_ENDED_MESSAGE)

    return RefreshOut(access_token=create_access_token(str(token.employee_id)))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutIn, db: Session = Depends(get_db)) -> None:
    token = db.scalars(
        select(RefreshToken).where(RefreshToken.token_hash == hash_secret(payload.refresh_token))
    ).first()

    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        db.commit()
