from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.payment import get_payment_provider

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.post("/upgrade")
def upgrade(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    provider = get_payment_provider(settings.payment_provider)
    result = provider.create_subscription(user.id)
    if result.get("status") != "active":
        raise HTTPException(status_code=400, detail="Upgrade failed")
    user.mode = "professional"
    db.commit()
    return {"message": "Professional access granted (demo)", "mode": user.mode, "payment": result}
