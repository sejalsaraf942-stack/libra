import datetime as dt
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    mode = Column(String(20), default="normal", nullable=False)
    warning_count = Column(Integer, default=0, nullable=False)
    suspended = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    consumed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(40), unique=True, index=True, nullable=False)
    extra_uses = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    uses_left = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    reason = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
