from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import Coupon

router = APIRouter(prefix="/coupons", tags=["coupons"])


class CouponIn(BaseModel):
    code: str
    extra_uses: int
    uses: int = 1
    days_valid: int = 30


@router.post("")
def create_coupon(payload: CouponIn, db: Session = Depends(get_db)):
    c = Coupon(code=payload.code, extra_uses=payload.extra_uses, uses_left=payload.uses,
               expires_at=datetime.utcnow() + timedelta(days=payload.days_valid))
    db.add(c)
    db.commit()
    return {"code": c.code, "uses_left": c.uses_left}


@router.post("/redeem")
def redeem(code: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.api.query import redeem_coupon
    return redeem_coupon(code, user, db)
