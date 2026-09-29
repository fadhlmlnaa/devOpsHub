import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import SessionLocal, check_db_connection
from app.core.logging_config import setup_logging
from app.services.alert_evaluation import AlertEvaluationService
from app.services.maintenance import MaintenanceService

setup_logging()
logger = logging.getLogger("devopshub.worker")

_is_running = True


def handle_stop_signals(signum, frame):
    global _is_running
    logger.info(f"Menerima sinyal {signal.Signals(signum).name}. Mematikan background worker dengan anggun...")
    _is_running = False


async def run_worker():
    global _is_running
    logger.info(f"DevOpsHub Background Worker dimulai (Env: {settings.APP_ENV})...")

    # Check initial database connectivity
    if not check_db_connection():
        logger.error("Gagal terhubung ke database PostgreSQL saat inisialisasi worker.")
    else:
        logger.info("Database PostgreSQL terhubung dengan sukses.")

    maintenance_counter = 0

    while _is_running:
        try:
            db = SessionLocal()
            try:
                # 1. Alert Evaluation
                alert_service = AlertEvaluationService(db)
                alert_summary = await alert_service.evaluate_workspace_rules()
                if alert_summary.get("alerts_triggered", 0) > 0 or alert_summary.get("alerts_resolved", 0) > 0:
                    logger.info(f"Worker alert evaluation: {alert_summary}")

                # 2. Retention Maintenance (Every ~1 hour / 60 iterations if interval=60s)
                maintenance_counter += 1
                if maintenance_counter >= 60:
                    maintenance_service = MaintenanceService(db)
                    cleanup_res = maintenance_service.cleanup_expired_records()
                    maintenance_counter = 0
            finally:
                db.close()

            # Sleep between evaluation cycles
            for _ in range(settings.ALERT_EVALUATION_INTERVAL_SECONDS):
                if not _is_running:
                    break
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error pada worker cycle: {e}", exc_info=True)
            await asyncio.sleep(10)

    logger.info("DevOpsHub Background Worker selesai dimatikan.")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_stop_signals)
    signal.signal(signal.SIGINT, handle_stop_signals)
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker dihentikan oleh user.")
        sys.exit(0)
