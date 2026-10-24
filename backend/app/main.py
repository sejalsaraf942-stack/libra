from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("libra.api")

from app.config import settings
from app.db.session import Base, engine
from app.api.auth import router as auth_router
from app.api.query import router as query_router
from app.api.subscription import router as sub_router
from app.api.coupons import router as coupons_router

app = FastAPI(title="Libra API", version="0.1.0")

from app.db.session import Base as _Base, engine as _engine  # noqa: E402
_Base.metadata.create_all(bind=_engine)  # noqa: E402

app.include_router(auth_router)
app.include_router(query_router)
app.include_router(sub_router)
app.include_router(coupons_router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error: %s", exc)
    origin = request.headers.get("origin")
    allowed_origin = origin if origin in origins else (origins[0] if origins else "*")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "mocked_services": {
            "otp": settings.otp_provider == "mock",
            "llm": settings.llm_provider == "mock",
            "payment": settings.payment_provider == "mock",
        },
    }
