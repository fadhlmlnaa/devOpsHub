import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import check_db_connection
from app.api.v1.router import api_v1_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Memulai DevOps Platform API Backend...")
    if check_db_connection():
        logger.info("Berhasil terhubung ke database PostgreSQL.")
    else:
        logger.warning("Gagal terhubung ke database PostgreSQL saat startup.")
    yield
    logger.info("Mematikan DevOps Platform API Backend...")


app = FastAPI(
    title="DevOps Mobile Platform API",
    description="Backend API untuk DevOps Mobile Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API v1 Router
app.include_router(api_v1_router)


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    db_connected = check_db_connection()
    return {
        "status": "ok",
        "database": "ok" if db_connected else "disconnected",
    }
