import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import check_db_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DevOps Platform API Backend...")
    if check_db_connection():
        logger.info("Successfully connected to PostgreSQL database.")
    else:
        logger.warning("Could not connect to PostgreSQL database on startup.")
    yield
    logger.info("Shutting down DevOps Platform API Backend...")


app = FastAPI(
    title="DevOps Mobile Platform API",
    description="Backend API for DevOps Mobile Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/api/v1/health")
def health_check():
    db_connected = check_db_connection()
    return {
        "status": "ok",
        "database": "ok" if db_connected else "disconnected",
    }
