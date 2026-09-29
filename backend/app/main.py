import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import check_db_connection, SessionLocal
from app.core.redis import check_redis_connection
from app.core.request_id import RequestIDMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.logging_config import setup_logging
from app.core.errors import register_exception_handlers
from app.api.v1.router import api_v1_router

# Setup application logging
setup_logging()
logger = logging.getLogger(__name__)


async def background_alert_scheduler():
    """Background task to evaluate alert rules on configured interval."""
    if not settings.ALERT_ENABLE_BACKGROUND_SCHEDULER:
        return

    from app.services.alert_evaluation import AlertEvaluationService

    logger.info(
        f"Background alert scheduler aktif (Interval: {settings.ALERT_EVALUATION_INTERVAL_SECONDS} detik)..."
    )
    # Give initial startup a few seconds before first check
    await asyncio.sleep(5)
    while True:
        try:
            db = SessionLocal()
            try:
                service = AlertEvaluationService(db)
                summary = await service.evaluate_workspace_rules()
                if summary.get("alerts_triggered", 0) > 0 or summary.get("alerts_resolved", 0) > 0:
                    logger.info(f"Alert evaluation: {summary}")
            finally:
                db.close()
            await asyncio.sleep(settings.ALERT_EVALUATION_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error pada background alert scheduler: {e}")
            await asyncio.sleep(settings.ALERT_EVALUATION_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Memulai DevOps Platform API Backend (Env: {settings.APP_ENV})...")

    # Production Startup Security Validation
    prod_errors = settings.validate_production_settings()
    if prod_errors:
        for err in prod_errors:
            logger.critical(f"FATAL STARTUP ERROR: {err}")
        if settings.is_production:
            raise RuntimeError(f"Startup digagalkan karena konfigurasi production tidak aman: {'; '.join(prod_errors)}")

    if check_db_connection():
        logger.info("Berhasil terhubung ke database PostgreSQL.")
    else:
        logger.warning("Gagal terhubung ke database PostgreSQL saat startup.")

    # Start background scheduler
    scheduler_task = asyncio.create_task(background_alert_scheduler())
    yield
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    logger.info("Mematikan DevOps Platform API Backend...")


app = FastAPI(
    title="DevOps Mobile Platform API",
    description="Backend API untuk DevOps Mobile Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

# Register Request ID Middleware (Outer)
app.add_middleware(RequestIDMiddleware)

# Add Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Enable CORS with configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True if settings.cors_origins != ["*"] else False,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$" if not settings.is_production else None,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Global Exception Handlers
register_exception_handlers(app)

# Include API v1 Router
app.include_router(api_v1_router)


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """General health check for backward compatibility."""
    db_connected = check_db_connection()
    return {
        "status": "ok",
        "database": "ok" if db_connected else "disconnected",
    }


@app.get("/api/v1/health/live", tags=["Health"])
def liveness_check():
    """Lightweight liveness probe indicating process is running."""
    return {
        "status": "ok",
        "app_env": settings.APP_ENV,
        "version": "1.0.0",
    }


@app.get("/api/v1/health/ready", tags=["Health"])
def readiness_check(response: Response):
    """Readiness probe checking critical dependencies (PostgreSQL, Redis)."""
    db_ok = check_db_connection()
    redis_ok = check_redis_connection()

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unavailable",
            "database": "disconnected",
            "redis": "connected" if redis_ok else "disconnected",
        }

    return {
        "status": "ready",
        "database": "connected",
        "redis": "connected" if redis_ok else "disconnected",
    }
