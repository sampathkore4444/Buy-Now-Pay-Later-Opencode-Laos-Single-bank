from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from core.config import settings
from core.logging import setup_logging
from core.redis import init_redis, close_redis
from core.kafka import init_kafka, close_kafka
from routes.api.v1 import (
    auth_router,
    auth_admin_router,
    merchants_router,
    consumers_router,
    staging_router,
    transactions_router,
    webhooks_router,
    refunds_router,
    disputes_router,
    settlements_router,
    eod_router,
    reconciliation_router,
    fees_router,
    fraud_rules_router,
    repayments_router,
    credit_router,
    notifications_router,
    complaints_router,
)
from services.metrics_service import MetricsMiddleware
from tasks.scheduler import start_scheduler
from common.exceptions import (
    NotFoundError,
    ConflictError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    InsufficientLimitError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_redis()
    await init_kafka()
    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)
    await close_kafka()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Single Bank Embedded BNPL Platform for Lao PDR",
    lifespan=lifespan,
)

app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(BadRequestError)
async def bad_request_handler(request: Request, exc: BadRequestError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(InsufficientLimitError)
async def insufficient_limit_handler(request: Request, exc: InsufficientLimitError):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


API_V1_PREFIX = "/api/v1"

app.include_router(auth_admin_router, prefix=API_V1_PREFIX)
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(merchants_router, prefix=API_V1_PREFIX)
app.include_router(consumers_router, prefix=API_V1_PREFIX)
app.include_router(staging_router, prefix=API_V1_PREFIX)
app.include_router(transactions_router, prefix=API_V1_PREFIX)
app.include_router(webhooks_router, prefix=API_V1_PREFIX)
app.include_router(refunds_router, prefix=API_V1_PREFIX)
app.include_router(disputes_router, prefix=API_V1_PREFIX)
app.include_router(settlements_router, prefix=API_V1_PREFIX)
app.include_router(eod_router, prefix=API_V1_PREFIX)
app.include_router(reconciliation_router, prefix=API_V1_PREFIX)
app.include_router(fees_router, prefix=API_V1_PREFIX)
app.include_router(fraud_rules_router, prefix=API_V1_PREFIX)
app.include_router(repayments_router, prefix=API_V1_PREFIX)
app.include_router(credit_router, prefix=API_V1_PREFIX)
app.include_router(notifications_router, prefix=API_V1_PREFIX)
app.include_router(complaints_router, prefix=API_V1_PREFIX)


@app.get("/health")
async def health():
    from core.database import BnplSessionLocal
    from core.redis import redis_client
    health_info = {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "checks": {},
    }
    try:
        db = BnplSessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_info["checks"]["database"] = "ok"
    except Exception as e:
        health_info["checks"]["database"] = f"error: {e}"
        health_info["status"] = "degraded"
    try:
        r = await redis_client
        await r.ping()
        health_info["checks"]["redis"] = "ok"
    except Exception as e:
        health_info["checks"]["redis"] = f"error: {e}"
        health_info["status"] = "degraded"
    return health_info


@app.get("/metrics")
async def metrics():
    import os, psutil
    info = {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "python_version": os.sys.version,
        "process_memory_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2) if hasattr(psutil, "Process") else 0,
    }
    return info
