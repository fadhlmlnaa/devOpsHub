import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.alert import (
    AlertRule,
    Alert,
    AlertEvent,
)
from app.models.server import Server
from app.models.deployment import Deployment
from app.models.backup import Backup
from app.services.notification_service import NotificationService
from app.services.monitoring import MonitoringService
from app.services.redaction import SecretRedactor

logger = logging.getLogger(__name__)


def evaluate_numeric_operator(
    value: float, operator: str, threshold: float
) -> bool:
    op = operator.upper()
    if op == "GREATER_THAN":
        return value > threshold
    elif op == "GREATER_THAN_OR_EQUAL":
        return value >= threshold
    elif op == "LESS_THAN":
        return value < threshold
    elif op == "LESS_THAN_OR_EQUAL":
        return value <= threshold
    elif op == "EQUAL":
        return abs(value - threshold) < 1e-4
    elif op == "NOT_EQUAL":
        return abs(value - threshold) >= 1e-4
    return False


class AlertEvaluationService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.monitoring_service = MonitoringService()
        self.redactor = SecretRedactor()

    def get_target_servers(self, rule: AlertRule) -> List[Server]:
        if rule.server_id:
            srv = (
                self.db.query(Server)
                .filter(
                    Server.id == rule.server_id,
                    Server.workspace_id == rule.workspace_id,
                    Server.is_active == True,
                )
                .first()
            )
            return [srv] if srv else []
        elif rule.environment_id:
            return (
                self.db.query(Server)
                .filter(
                    Server.environment_id == rule.environment_id,
                    Server.workspace_id == rule.workspace_id,
                    Server.is_active == True,
                )
                .all()
            )
        else:
            return (
                self.db.query(Server)
                .filter(
                    Server.workspace_id == rule.workspace_id,
                    Server.is_active == True,
                )
                .all()
            )

    async def evaluate_rule_for_server(
        self,
        rule: AlertRule,
        server: Server,
        metric_override: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[float], str, str]:
        """
        Evaluates a single rule for a specific server.
        Returns: (is_condition_met, current_value, alert_title, alert_message)
        """
        metric_type = rule.metric_type.upper()
        now = datetime.utcnow()

        if metric_type in ("CPU_USAGE", "MEMORY_USAGE", "DISK_USAGE", "LOAD_AVERAGE"):
            # Fetch real-time telemetry or use mock/override for testing
            metrics = None
            if metric_override is not None:
                metrics = metric_override
            else:
                try:
                    res = await self.monitoring_service.get_server_metrics(server)
                    metrics = res.model_dump()
                except Exception as e:
                    logger.warning(f"Could not fetch metrics for alert evaluation on server {server.name}: {e}")

            if not metrics or metrics.get("status") == "OFFLINE":
                if metric_type == "SERVER_STATUS":
                    pass # handled below
                else:
                    return False, None, "", ""

            if metric_type == "CPU_USAGE":
                cpu_val = metrics.get("cpu", {}).get("usage_percent")
                if cpu_val is None:
                    return False, None, "", ""
                is_met = evaluate_numeric_operator(cpu_val, rule.operator, rule.threshold)
                title = f"Penggunaan CPU Tinggi ({server.name})"
                msg = f"Penggunaan CPU pada server {server.name} ({server.ip_address}) mencapai {cpu_val:.1f}% (Threshold: {rule.threshold:.1f}%)."
                return is_met, cpu_val, title, msg

            elif metric_type == "MEMORY_USAGE":
                mem_val = metrics.get("memory", {}).get("usage_percent")
                if mem_val is None:
                    return False, None, "", ""
                is_met = evaluate_numeric_operator(mem_val, rule.operator, rule.threshold)
                title = f"Penggunaan RAM / Memory Tinggi ({server.name})"
                msg = f"Penggunaan Memory pada server {server.name} ({server.ip_address}) mencapai {mem_val:.1f}% (Threshold: {rule.threshold:.1f}%)."
                return is_met, mem_val, title, msg

            elif metric_type == "DISK_USAGE":
                disk_val = metrics.get("disk", {}).get("usage_percent")
                if disk_val is None:
                    return False, None, "", ""
                is_met = evaluate_numeric_operator(disk_val, rule.operator, rule.threshold)
                title = f"Kapasitas Disk Kritis ({server.name})"
                msg = f"Penggunaan penyimpanan partisi utama pada server {server.name} mencapai {disk_val:.1f}% (Threshold: {rule.threshold:.1f}%)."
                return is_met, disk_val, title, msg

            elif metric_type == "LOAD_AVERAGE":
                load_val = metrics.get("load", {}).get("load1m")
                if load_val is None:
                    return False, None, "", ""
                is_met = evaluate_numeric_operator(load_val, rule.operator, rule.threshold)
                title = f"Load Average Tinggi ({server.name})"
                msg = f"Load average (1m) pada server {server.name} mencapai {load_val:.2f} (Threshold: {rule.threshold:.2f})."
                return is_met, load_val, title, msg

        elif metric_type == "SERVER_STATUS":
            # 0.0 = OFFLINE, 1.0 = ONLINE
            current_status = metric_override.get("status") if metric_override else server.status
            is_offline = (current_status.upper() == "OFFLINE")
            # If threshold is 0 (OFFLINE) and operator is EQUAL
            val = 0.0 if is_offline else 1.0
            is_met = evaluate_numeric_operator(val, rule.operator, rule.threshold)
            title = f"Server OFFLINE ({server.name})"
            msg = f"Server {server.name} ({server.ip_address}) terdeteksi OFFLINE atau tidak dapat dijangkau melalui SSH."
            return is_met, val, title, msg

        elif metric_type == "SERVICE_STATUS":
            # Check service status (0.0 = FAILED/STOPPED, 1.0 = RUNNING)
            svc_name = rule.target_identifier or "service"
            status_val = 1.0
            if metric_override and "service_status" in metric_override:
                status_val = float(metric_override["service_status"])
            elif metric_override and "services" in metric_override:
                services_dict = metric_override.get("services") or {}
                svc_info = services_dict.get(svc_name, {})
                svc_st = svc_info.get("status", "") if isinstance(svc_info, dict) else str(svc_info)
                if svc_st.lower() in ("failed", "inactive", "stopped", "0", "0.0", "error"):
                    status_val = 0.0
            is_met = evaluate_numeric_operator(status_val, rule.operator, rule.threshold)
            title = f"Service {svc_name} Gagal ({server.name})"
            msg = f"Layanan systemd '{svc_name}' pada server {server.name} mengalami kegagalan / state tidak aktif."
            return is_met, status_val, title, msg

        elif metric_type == "DEPLOYMENT_STATUS":
            # Check latest deployment on this server or workspace
            latest_dep = (
                self.db.query(Deployment)
                .filter(
                    Deployment.workspace_id == rule.workspace_id,
                    Deployment.server_id == server.id,
                )
                .order_by(Deployment.created_at.desc())
                .first()
            )
            val = 1.0
            if latest_dep and latest_dep.status.upper() == "FAILED":
                # Check if failure occurred recently (within last 1 hour)
                if (now - latest_dep.created_at).total_seconds() < 3600:
                    val = 0.0

            if metric_override and "deployment_status" in metric_override:
                val = metric_override["deployment_status"]

            is_met = evaluate_numeric_operator(val, rule.operator, rule.threshold)
            title = f"Deployment Gagal ({server.name})"
            msg = f"Eksekusi deployment pada server {server.name} mengalami kegagalan (FAILED)."
            return is_met, val, title, msg

        elif metric_type == "BACKUP_STATUS":
            # Check latest backup on this server or workspace
            latest_bak = (
                self.db.query(Backup)
                .filter(
                    Backup.workspace_id == rule.workspace_id,
                    Backup.server_id == server.id,
                )
                .order_by(Backup.created_at.desc())
                .first()
            )
            val = 1.0
            if latest_bak and latest_bak.status.upper() == "FAILED":
                if (now - latest_bak.created_at).total_seconds() < 3600:
                    val = 0.0

            if metric_override and "backup_status" in metric_override:
                val = metric_override["backup_status"]

            is_met = evaluate_numeric_operator(val, rule.operator, rule.threshold)
            title = f"Operasi Backup Gagal ({server.name})"
            msg = f"Operasi pencadangan data (backup) pada server {server.name} mengalami kegagalan (FAILED)."
            return is_met, val, title, msg

        return False, None, "", ""

    async def evaluate_workspace_rules(
        self,
        workspace_id: Optional[UUID] = None,
        metric_overrides: Optional[Dict[UUID, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Main evaluation loop: evaluates all active rules across workspace(s).
        Handles deduplication, duration thresholding, resolution, and spam-free notification dispatch.
        """
        now = datetime.utcnow()
        query = self.db.query(AlertRule).filter(AlertRule.is_enabled == True)
        if workspace_id:
            query = query.filter(AlertRule.workspace_id == workspace_id)

        rules = query.all()
        summary = {
            "rules_evaluated": len(rules),
            "alerts_triggered": 0,
            "alerts_resolved": 0,
            "notifications_sent": 0,
            "errors": [],
        }

        for rule in rules:
            servers = self.get_target_servers(rule)
            for server in servers:
                try:
                    server_override = (
                        metric_overrides.get(server.id)
                        if metric_overrides
                        else None
                    )
                    (
                        is_condition_met,
                        current_val,
                        title,
                        message,
                    ) = await self.evaluate_rule_for_server(
                        rule, server, server_override
                    )

                    # Find existing active FIRING alert for this (rule, server)
                    existing_alert = (
                        self.db.query(Alert)
                        .filter(
                            Alert.alert_rule_id == rule.id,
                            Alert.server_id == server.id,
                            Alert.status == "FIRING",
                        )
                        .first()
                    )

                    if is_condition_met:
                        if existing_alert:
                            # Alert is already firing -> DEDUPLICATION: update evaluation timestamp
                            existing_alert.last_evaluated_at = now
                            existing_alert.current_value = current_val

                            # Check if duration is met and notification not yet sent
                            if existing_alert.notification_sent_at is None:
                                elapsed = (now - existing_alert.triggered_at).total_seconds()
                                if elapsed >= rule.duration_seconds:
                                    sent = await self.notification_service.dispatch_alert_notification(
                                        existing_alert, is_resolution=False
                                    )
                                    existing_alert.notification_sent_at = now
                                    event = AlertEvent(
                                        alert_id=existing_alert.id,
                                        event_type="NOTIFICATION_SENT",
                                        message=f"Notifikasi peringatan dikirim ke member workspace (Durasi {rule.duration_seconds}s terpenuhi).",
                                    )
                                    self.db.add(event)
                                    summary["notifications_sent"] += sent

                            self.db.commit()
                        else:
                            # New condition breach -> create Alert record
                            should_notify_immediately = (rule.duration_seconds == 0)

                            new_alert = Alert(
                                workspace_id=rule.workspace_id,
                                alert_rule_id=rule.id,
                                environment_id=server.environment_id,
                                server_id=server.id,
                                status="FIRING",
                                severity=rule.severity,
                                title=title,
                                message=message,
                                current_value=current_val,
                                threshold_value=rule.threshold,
                                triggered_at=now,
                                last_evaluated_at=now,
                                notification_sent_at=now if should_notify_immediately else None,
                            )
                            self.db.add(new_alert)
                            self.db.flush()

                            # Audit event TRIGGERED
                            event_triggered = AlertEvent(
                                alert_id=new_alert.id,
                                event_type="TRIGGERED",
                                message=f"Peringatan dipicu: {message}",
                            )
                            self.db.add(event_triggered)

                            if should_notify_immediately:
                                sent = await self.notification_service.dispatch_alert_notification(
                                    new_alert, is_resolution=False
                                )
                                event_notif = AlertEvent(
                                    alert_id=new_alert.id,
                                    event_type="NOTIFICATION_SENT",
                                    message="Notifikasi awal dikirim ke member workspace.",
                                )
                                self.db.add(event_notif)
                                summary["notifications_sent"] += sent

                            self.db.commit()
                            summary["alerts_triggered"] += 1

                    else:
                        # Condition is NOT met -> check if we need to resolve an existing FIRING alert
                        if existing_alert:
                            existing_alert.status = "RESOLVED"
                            existing_alert.resolved_at = now
                            existing_alert.last_evaluated_at = now
                            existing_alert.current_value = current_val

                            # Audit event RESOLVED
                            event_resolved = AlertEvent(
                                alert_id=existing_alert.id,
                                event_type="RESOLVED",
                                message=f"Kondisi peringatan pulih normal (Nilai saat ini: {current_val}).",
                            )
                            self.db.add(event_resolved)

                            # Send resolution notification only if a firing notification was previously sent
                            if existing_alert.notification_sent_at is not None:
                                sent = await self.notification_service.dispatch_alert_notification(
                                    existing_alert, is_resolution=True
                                )
                                event_notif = AlertEvent(
                                    alert_id=existing_alert.id,
                                    event_type="NOTIFICATION_SENT",
                                    message="Notifikasi pemulihan (RESOLVED) dikirim ke member workspace.",
                                )
                                self.db.add(event_notif)
                                summary["notifications_sent"] += sent

                            self.db.commit()
                            summary["alerts_resolved"] += 1

                except Exception as e:
                    logger.error(f"Error evaluating rule {rule.id} on server {server.id}: {e}")
                    summary["errors"].append(str(e))
                    self.db.rollback()

        return summary

    async def resolve_alert_manually(
        self,
        alert_id: UUID,
        workspace_id: UUID,
        user_id: UUID,
        confirm: bool,
    ) -> Alert:
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resolusi alert memerlukan konfirmasi eksplisit (confirm: true).",
            )

        alert = (
            self.db.query(Alert)
            .filter(
                Alert.id == alert_id,
                Alert.workspace_id == workspace_id,
            )
            .first()
        )
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert tidak ditemukan pada workspace ini.",
            )

        if alert.status == "RESOLVED":
            return alert

        now = datetime.utcnow()
        alert.status = "RESOLVED"
        alert.resolved_at = now
        alert.last_evaluated_at = now

        event_resolved = AlertEvent(
            alert_id=alert.id,
            event_type="RESOLVED",
            message=f"Peringatan diselesaikan secara manual oleh pengguna (User ID: {user_id}). Aturan alert tetap aktif.",
        )
        self.db.add(event_resolved)

        if alert.notification_sent_at is not None:
            await self.notification_service.dispatch_alert_notification(
                alert, is_resolution=True
            )
            event_notif = AlertEvent(
                alert_id=alert.id,
                event_type="NOTIFICATION_SENT",
                message="Notifikasi resolusi manual dikirim ke member workspace.",
            )
            self.db.add(event_notif)

        self.db.commit()
        self.db.refresh(alert)
        return alert
