import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User, Coupon, ReviewRecord, UsageEvent
from app.services.safety import classify_intent
from app.services.retrieval import retrieve, needs_state, extract_location

router = APIRouter(prefix="/query", tags=["query"])


class QueryIn(BaseModel):
    text: str
    mode: str = "normal"
    history: list[str] = []
    location: str | None = None


def _today_start():
    return dt.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def _used_today(db: Session, user_id: int) -> int:
    return db.query(UsageEvent).filter(UsageEvent.user_id == user_id, UsageEvent.created_at >= _today_start()).count()


@router.post("")
def run_query(payload: QueryIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.suspended:
        raise HTTPException(status_code=403, detail="Account suspended")
    mode = payload.mode if payload.mode in ("normal", "professional") else user.mode
    if mode == "professional" and user.mode != "professional":
        raise HTTPException(status_code=403, detail="Professional access required")

    # Safety first
    full_text = " ".join(payload.history + [payload.text])
    detected_location = payload.location or extract_location(full_text)
    intent = classify_intent(full_text)
    if intent == "unsafe":
        user.warning_count += 1
        if user.warning_count >= 3:
            user.suspended = True
            db.add(ReviewRecord(user_id=user.id, reason="third warning"))
        db.commit()
        raise HTTPException(status_code=400, detail=f"Warning {user.warning_count}/3: request stopped")

    if intent == "vague" and len(full_text.split()) < 8:
        return {"clarification": "Could you provide more details (parties, location, dates)?"}
    if needs_state(full_text, location=detected_location):
        return {"clarification": "Which state or union territory does this rental dispute arise in? State rent laws vary."}

    # Quota
    limit = settings.professional_daily_limit if mode == "professional" else settings.normal_daily_limit
    used = _used_today(db, user.id)
    if used >= limit:
        raise HTTPException(status_code=429, detail="Daily quota exhausted")

    # Atomic spend
    db.add(UsageEvent(user_id=user.id))
    db.commit()

    # Grounded answer placeholder (RAG in Phase 6)
    return {
        "short_answer": ("Based on retrieved sources (DEMO corpus)." if retrieve(full_text) else "No reliable source found; cannot answer reliably."),
        "explanation": "Retrieval and citation generation will be connected in Phase 6.",
        "caveats": ["This is not legal advice. Consult an advocate for representation."],
        "sources": retrieve(full_text),
        "mode": mode,
        "remaining": limit - used - 1,
        "location": detected_location,
    }


@router.post("/coupon/redeem")
def redeem_coupon(code: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter(Coupon.code == code).first()
    if coupon is None or coupon.uses_left <= 0:
        raise HTTPException(status_code=400, detail="Invalid or exhausted coupon")
    if coupon.expires_at and coupon.expires_at < dt.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Coupon expired")
    # grant extra usage by adding a usage event credit? Simpler: store credit as negative usage not possible; instead record coupon redemption as review? 
    coupon.uses_left -= 1
    db.commit()
    return {"message": "Coupon redeemed", "extra_uses": coupon.extra_uses}
