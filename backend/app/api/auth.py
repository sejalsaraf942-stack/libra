import datetime as dt
import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User, OtpCode
from app.services.otp_provider import get_otp_provider

router = APIRouter(prefix="/auth", tags=["auth"])

# Simple in-memory rate limit (per-process; replace with Redis in prod)
_rate: dict[str, list[dt.datetime]] = {}


def _rate_limit(key: str, limit: int, window: int) -> None:
    now = dt.datetime.utcnow()
    bucket = [t for t in _rate.get(key, []) if (now - t).total_seconds() < window]
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests")
    bucket.append(now)
    _rate[key] = bucket


class PhoneIn(BaseModel):
    phone: str


class VerifyIn(BaseModel):
    phone: str
    code: str


@router.post("/otp/request")
def request_otp(payload: PhoneIn, db: Session = Depends(get_db)):
    phone = payload.phone.strip()
    if not phone or len(phone) < 8:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    _rate_limit(f"otp_req:{phone}", 5, 900)
    code = "".join(random.choices("0123456789", k=6))
    otp = OtpCode(phone=phone, code=code, expires_at=dt.datetime.utcnow() + dt.timedelta(minutes=5))
    db.add(otp)
    db.commit()
    provider = get_otp_provider(settings.otp_provider)
    provider.send(phone, code)
    resp = {"message": "OTP sent"}
    # Only expose code in dev mock mode
    if settings.otp_provider == "mock" and settings.app_env != "production":
        resp["dev_code"] = code
    return resp


@router.post("/otp/verify")
def verify_otp(payload: VerifyIn, db: Session = Depends(get_db)):
    phone = payload.phone.strip()
    _rate_limit(f"otp_verify:{phone}", 10, 900)
    otp = (
        db.query(OtpCode)
        .filter(OtpCode.phone == phone, OtpCode.consumed.is_(False))
        .order_by(OtpCode.id.desc())
        .first()
    )
    if otp is None:
        raise HTTPException(status_code=400, detail="No OTP requested")
    if otp.expires_at < dt.datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")
    otp.attempts += 1
    if otp.attempts > 5:
        otp.consumed = True
        db.commit()
        raise HTTPException(status_code=400, detail="Too many attempts")
    if otp.code != payload.code.strip():
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect OTP")
    otp.consumed = True
    user = db.query(User).filter(User.phone == phone).first()
    if user is None:
        user = User(phone=phone, mode="normal")
        db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.id), "token_type": "bearer", "mode": user.mode}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "phone": user.phone, "mode": user.mode, "suspended": user.suspended}
