import pytest
from datetime import datetime, timedelta, timezone
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.models.environment import Environment
from app.models.server import Server
from app.models.alert import (
    AlertRule,
    Alert,
    AlertEvent,
    NotificationPreference,
    Notification,
)
from app.models.deployment import Deployment, DeploymentConfig
from app.models.backup import Backup, BackupConfig
from app.services.alert_evaluation import AlertEvaluationService


@pytest.fixture
def test_setup(db_session: Session):
    owner = User(
        email=f"alert_owner_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="$2b$12$eX4mP1eH4sH.h4sH3d.P4ssw0rdH4shValue1234567890",
        name="Alert Owner",
        is_active=True,
    )
    admin = User(
        email=f"alert_admin_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="$2b$12$eX4mP1eH4sH.h4sH3d.P4ssw0rdH4shValue1234567890",
        name="Alert Admin",
        is_active=True,
    )
    dev = User(
        email=f"alert_dev_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="$2b$12$eX4mP1eH4sH.h4sH3d.P4ssw0rdH4shValue1234567890",
        name="Alert Dev",
        is_active=True,
    )
    viewer = User(
        email=f"alert_viewer_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="$2b$12$eX4mP1eH4sH.h4sH3d.P4ssw0rdH4shValue1234567890",
        name="Alert Viewer",
        is_active=True,
    )
    other_user = User(
        email=f"alert_other_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="$2b$12$eX4mP1eH4sH.h4sH3d.P4ssw0rdH4shValue1234567890",
        name="Other User",
        is_active=True,
    )
    db_session.add_all([owner, admin, dev, viewer, other_user])
    db_session.commit()

    ws = Workspace(name="Alert Workspace")
    ws_other = Workspace(name="Other Alert Workspace")
    db_session.add_all([ws, ws_other])
    db_session.commit()

    mem_owner = WorkspaceMember(workspace_id=ws.id, user_id=owner.id, role=WorkspaceRole.OWNER)
    mem_admin = WorkspaceMember(workspace_id=ws.id, user_id=admin.id, role=WorkspaceRole.ADMIN)
    mem_dev = WorkspaceMember(workspace_id=ws.id, user_id=dev.id, role=WorkspaceRole.DEVELOPER)
    mem_viewer = WorkspaceMember(workspace_id=ws.id, user_id=viewer.id, role=WorkspaceRole.VIEWER)
    mem_other = WorkspaceMember(workspace_id=ws_other.id, user_id=other_user.id, role=WorkspaceRole.OWNER)
    db_session.add_all([mem_owner, mem_admin, mem_dev, mem_viewer, mem_other])

    env = Environment(workspace_id=ws.id, name="Production", key="prod", is_protected=True)
    db_session.add(env)
    db_session.commit()

    server = Server(
        workspace_id=ws.id,
        environment_id=env.id,
        name="prod-server-01",
        hostname="prod-01.internal",
        ip_address="192.168.1.100",
        ssh_port=22,
        username="admin",
        is_active=True,
    )
    db_session.add(server)
    db_session.commit()

    return {
        "owner": owner,
        "admin": admin,
        "dev": dev,
        "viewer": viewer,
        "other_user": other_user,
        "workspace": ws,
        "workspace_other": ws_other,
        "environment": env,
        "server": server,
        "headers_owner": {"Authorization": f"Bearer {create_access_token(str(owner.id))}"},
        "headers_admin": {"Authorization": f"Bearer {create_access_token(str(admin.id))}"},
        "headers_dev": {"Authorization": f"Bearer {create_access_token(str(dev.id))}"},
        "headers_viewer": {"Authorization": f"Bearer {create_access_token(str(viewer.id))}"},
        "headers_other": {"Authorization": f"Bearer {create_access_token(str(other_user.id))}"},
    }


def test_alert_rule_crud_and_rbac(client: TestClient, test_setup: dict, db_session: Session):
    headers_owner = test_setup["headers_owner"]
    headers_admin = test_setup["headers_admin"]
    headers_dev = test_setup["headers_dev"]
    headers_viewer = test_setup["headers_viewer"]
    headers_other = test_setup["headers_other"]
    ws = test_setup["workspace"]
    ws_other = test_setup["workspace_other"]
    env = test_setup["environment"]
    server = test_setup["server"]

    # 1. Create rule as OWNER
    rule_data = {
        "name": "High CPU Alert",
        "description": "Trigger when CPU exceeds 85%",
        "metric_type": "CPU_USAGE",
        "operator": "GREATER_THAN",
        "threshold": 85.0,
        "duration_seconds": 60,
        "severity": "CRITICAL",
        "environment_id": str(env.id),
        "server_id": str(server.id),
        "is_enabled": True,
    }

    res = client.post(f"/api/v1/workspaces/{ws.id}/alert-rules", json=rule_data, headers=headers_owner)
    assert res.status_code == 201, res.text
    created = res.json()
    assert created["name"] == "High CPU Alert"
    assert created["metric_type"] == "CPU_USAGE"
    assert created["threshold"] == 85.0
    rule_id = created["id"]

    # 2. Admin can create rule
    rule_data_mem = {
        "name": "High Memory Alert",
        "metric_type": "MEMORY_USAGE",
        "operator": "GREATER_THAN_OR_EQUAL",
        "threshold": 90.0,
        "duration_seconds": 120,
        "severity": "WARNING",
        "is_enabled": True,
    }
    res_admin = client.post(f"/api/v1/workspaces/{ws.id}/alert-rules", json=rule_data_mem, headers=headers_admin)
    assert res_admin.status_code == 201

    # 3. Viewer and Developer cannot create rule (403)
    res_v = client.post(f"/api/v1/workspaces/{ws.id}/alert-rules", json=rule_data, headers=headers_viewer)
    assert res_v.status_code == 403
    res_d = client.post(f"/api/v1/workspaces/{ws.id}/alert-rules", json=rule_data, headers=headers_dev)
    assert res_d.status_code == 403

    # 4. List rules (all workspace members can read)
    res_list = client.get(f"/api/v1/workspaces/{ws.id}/alert-rules", headers=headers_viewer)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 2

    # 5. Workspace isolation: other user cannot see rules of ws
    res_other = client.get(f"/api/v1/workspaces/{ws.id}/alert-rules", headers=headers_other)
    assert res_other.status_code in (403, 404)

    # 6. Update rule as OWNER
    res_up = client.patch(
        f"/api/v1/workspaces/{ws.id}/alert-rules/{rule_id}",
        json={"threshold": 90.0, "severity": "CRITICAL"},
        headers=headers_owner,
    )
    assert res_up.status_code == 200
    assert res_up.json()["threshold"] == 90.0

    # 7. Delete rule as VIEWER (403) vs OWNER (204)
    res_del_v = client.delete(f"/api/v1/workspaces/{ws.id}/alert-rules/{rule_id}", headers=headers_viewer)
    assert res_del_v.status_code == 403

    res_del = client.delete(f"/api/v1/workspaces/{ws.id}/alert-rules/{rule_id}", headers=headers_owner)
    assert res_del.status_code == 204


def test_alert_rule_validation(client: TestClient, test_setup: dict):
    headers_owner = test_setup["headers_owner"]
    ws = test_setup["workspace"]

    # Invalid threshold for percentage metric (> 100)
    res = client.post(
        f"/api/v1/workspaces/{ws.id}/alert-rules",
        json={
            "name": "Invalid CPU",
            "metric_type": "CPU_USAGE",
            "operator": "GREATER_THAN",
            "threshold": 150.0,
            "duration_seconds": 60,
            "severity": "WARNING",
        },
        headers=headers_owner,
    )
    assert res.status_code == 422

    # Negative threshold for percentage
    res2 = client.post(
        f"/api/v1/workspaces/{ws.id}/alert-rules",
        json={
            "name": "Invalid Memory",
            "metric_type": "MEMORY_USAGE",
            "operator": "GREATER_THAN",
            "threshold": -5.0,
            "duration_seconds": 60,
            "severity": "WARNING",
        },
        headers=headers_owner,
    )
    assert res2.status_code == 422

    # Negative duration
    res3 = client.post(
        f"/api/v1/workspaces/{ws.id}/alert-rules",
        json={
            "name": "Invalid Duration",
            "metric_type": "CPU_USAGE",
            "operator": "GREATER_THAN",
            "threshold": 80.0,
            "duration_seconds": -10,
            "severity": "WARNING",
        },
        headers=headers_owner,
    )
    assert res3.status_code == 422


@pytest.mark.asyncio
async def test_alert_evaluation_trigger_and_deduplication(db_session: Session, test_setup: dict):
    ws = test_setup["workspace"]
    server = test_setup["server"]

    rule = AlertRule(
        workspace_id=ws.id,
        name="High CPU Test Rule",
        metric_type="CPU_USAGE",
        operator="GREATER_THAN",
        threshold=80.0,
        duration_seconds=0,  # Immediate trigger
        severity="CRITICAL",
        server_id=server.id,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)

    eval_service = AlertEvaluationService(db_session)

    # 1. First evaluation with CPU = 95% -> creates Alert and notification
    metric_high = {"cpu": {"usage_percent": 95.0}, "status": "ONLINE"}
    summary1 = await eval_service.evaluate_workspace_rules(
        workspace_id=ws.id, metric_overrides={server.id: metric_high}
    )
    assert summary1["alerts_triggered"] == 1
    assert summary1["notifications_sent"] >= 1

    alerts = db_session.query(Alert).filter(Alert.alert_rule_id == rule.id).all()
    assert len(alerts) == 1
    firing_alert = alerts[0]
    assert firing_alert.status == "FIRING"
    assert firing_alert.severity == "CRITICAL"
    assert firing_alert.current_value == 95.0

    # 2. Second evaluation with CPU = 92% (still high) -> DEDUPLICATION: Alert count remains 1, no duplicate notification
    metric_still_high = {"cpu": {"usage_percent": 92.0}, "status": "ONLINE"}
    summary2 = await eval_service.evaluate_workspace_rules(
        workspace_id=ws.id, metric_overrides={server.id: metric_still_high}
    )
    assert summary2["alerts_triggered"] == 0  # No new alert created
    assert summary2["notifications_sent"] == 0  # No duplicate notification

    alerts_after = db_session.query(Alert).filter(Alert.alert_rule_id == rule.id).all()
    assert len(alerts_after) == 1  # Deduplication verified!

    # 3. Third evaluation with CPU = 50% (normal) -> RESOLUTION: status becomes RESOLVED
    metric_normal = {"cpu": {"usage_percent": 50.0}, "status": "ONLINE"}
    summary3 = await eval_service.evaluate_workspace_rules(
        workspace_id=ws.id, metric_overrides={server.id: metric_normal}
    )
    assert summary3["alerts_resolved"] == 1
    assert summary3["notifications_sent"] >= 1

    db_session.refresh(firing_alert)
    assert firing_alert.status == "RESOLVED"
    assert firing_alert.resolved_at is not None

    # 4. Fourth evaluation CPU = 96% -> can fire again after resolution!
    summary4 = await eval_service.evaluate_workspace_rules(
        workspace_id=ws.id, metric_overrides={server.id: metric_high}
    )
    assert summary4["alerts_triggered"] == 1
    alerts_refired = db_session.query(Alert).filter(Alert.alert_rule_id == rule.id, Alert.status == "FIRING").all()
    assert len(alerts_refired) == 1


@pytest.mark.asyncio
async def test_alert_duration_threshold(db_session: Session, test_setup: dict):
    ws = test_setup["workspace"]
    server = test_setup["server"]

    rule = AlertRule(
        workspace_id=ws.id,
        name="Delayed Memory Alert",
        metric_type="MEMORY_USAGE",
        operator="GREATER_THAN",
        threshold=80.0,
        duration_seconds=300,  # 5 minutes duration
        severity="WARNING",
        server_id=server.id,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)

    eval_service = AlertEvaluationService(db_session)

    # 1. Condition breached -> Alert FIRING created, but notification NOT sent yet (duration > 0)
    metric_breach = {"memory": {"usage_percent": 88.0}, "status": "ONLINE"}
    summary1 = await eval_service.evaluate_workspace_rules(
        workspace_id=ws.id, metric_overrides={server.id: metric_breach}
    )
    assert summary1["alerts_triggered"] == 1
    assert summary1["notifications_sent"] == 0

    alert = db_session.query(Alert).filter(Alert.alert_rule_id == rule.id).first()
    assert alert.status == "FIRING"
    assert alert.notification_sent_at is None

    # Simulate elapsed time (backdate triggered_at by 310 seconds)
    alert.triggered_at = datetime.now(timezone.utc) - timedelta(seconds=310)
    db_session.commit()

    # 2. Re-evaluating after duration elapsed -> notification sent
    summary2 = await eval_service.evaluate_workspace_rules(
        workspace_id=ws.id, metric_overrides={server.id: metric_breach}
    )
    assert summary2["notifications_sent"] >= 1
    db_session.refresh(alert)
    assert alert.notification_sent_at is not None


@pytest.mark.asyncio
async def test_server_offline_and_service_failure_evaluation(db_session: Session, test_setup: dict):
    ws = test_setup["workspace"]
    server = test_setup["server"]

    # Rule 1: Server OFFLINE
    rule_srv = AlertRule(
        workspace_id=ws.id,
        name="Server Offline Alert",
        metric_type="SERVER_STATUS",
        operator="EQUAL",
        threshold=0.0,  # OFFLINE
        duration_seconds=0,
        severity="CRITICAL",
        server_id=server.id,
        is_enabled=True,
    )
    # Rule 2: Service FAILED
    rule_svc = AlertRule(
        workspace_id=ws.id,
        name="Nginx Failed Alert",
        metric_type="SERVICE_STATUS",
        target_identifier="nginx",
        operator="EQUAL",
        threshold=0.0,  # 0.0 = failed / inactive
        duration_seconds=0,
        severity="CRITICAL",
        server_id=server.id,
        is_enabled=True,
    )
    db_session.add_all([rule_srv, rule_svc])
    db_session.commit()

    eval_service = AlertEvaluationService(db_session)

    # Simulate server offline & nginx failed
    telemetry = {
        "status": "OFFLINE",
        "services": {"nginx": {"status": "failed"}},
    }
    summary = await eval_service.evaluate_workspace_rules(
        workspace_id=ws.id, metric_overrides={server.id: telemetry}
    )
    assert summary["alerts_triggered"] == 2

    srv_alert = db_session.query(Alert).filter(Alert.alert_rule_id == rule_srv.id).first()
    assert srv_alert is not None
    assert srv_alert.status == "FIRING"
    assert "offline" in srv_alert.title.lower()

    svc_alert = db_session.query(Alert).filter(Alert.alert_rule_id == rule_svc.id).first()
    assert svc_alert is not None
    assert svc_alert.status == "FIRING"
    assert "nginx" in svc_alert.title.lower()


def test_notifications_and_preferences_api(client: TestClient, test_setup: dict, db_session: Session):
    owner = test_setup["owner"]
    viewer = test_setup["viewer"]
    headers_owner = test_setup["headers_owner"]
    headers_viewer = test_setup["headers_viewer"]
    ws = test_setup["workspace"]

    # 1. Get default notification preferences
    res_pref = client.get(f"/api/v1/workspaces/{ws.id}/notification-preferences", headers=headers_viewer)
    assert res_pref.status_code == 200
    assert res_pref.json()["in_app_enabled"] is True
    assert res_pref.json()["minimum_severity"] == "INFO"

    # 2. Update preference to CRITICAL only
    res_up_pref = client.patch(
        f"/api/v1/workspaces/{ws.id}/notification-preferences",
        json={"minimum_severity": "CRITICAL"},
        headers=headers_viewer,
    )
    assert res_up_pref.status_code == 200
    assert res_up_pref.json()["minimum_severity"] == "CRITICAL"

    # 3. Create a test notification for owner
    notif = Notification(
        user_id=owner.id,
        workspace_id=ws.id,
        title="Test Notification",
        message="Server disk is running low.",
        severity="WARNING",
        is_read=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    # 4. Check unread count
    res_count = client.get(f"/api/v1/workspaces/{ws.id}/notifications/unread-count", headers=headers_owner)
    assert res_count.status_code == 200
    assert res_count.json()["unread_count"] >= 1

    # 5. Mark notification as read
    res_read = client.patch(
        f"/api/v1/workspaces/{ws.id}/notifications/{notif.id}/read",
        headers=headers_owner,
    )
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # 6. User isolation: Viewer cannot mark owner's notification as read (404)
    res_read_v = client.patch(
        f"/api/v1/workspaces/{ws.id}/notifications/{notif.id}/read",
        headers=headers_viewer,
    )
    assert res_read_v.status_code == 404

    # 7. Mark all read
    res_mark_all = client.post(f"/api/v1/workspaces/{ws.id}/notifications/mark-all-read", headers=headers_owner)
    assert res_mark_all.status_code == 200


def test_manual_alert_resolution(client: TestClient, test_setup: dict, db_session: Session):
    headers_owner = test_setup["headers_owner"]
    headers_viewer = test_setup["headers_viewer"]
    ws = test_setup["workspace"]
    server = test_setup["server"]

    rule = AlertRule(
        workspace_id=ws.id,
        name="Offline Server Rule",
        metric_type="SERVER_STATUS",
        operator="EQUAL",
        threshold=0.0,  # 0.0 = OFFLINE
        duration_seconds=0,
        severity="CRITICAL",
        server_id=server.id,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)

    alert = Alert(
        workspace_id=ws.id,
        alert_rule_id=rule.id,
        server_id=server.id,
        status="FIRING",
        severity="CRITICAL",
        title="Server OFFLINE",
        message="Server prod-server-01 is unreachable.",
        triggered_at=datetime.now(timezone.utc),
        last_evaluated_at=datetime.now(timezone.utc),
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)

    # Viewer cannot manually resolve (403)
    res_v = client.post(
        f"/api/v1/workspaces/{ws.id}/alerts/{alert.id}/resolve",
        json={"confirm": True},
        headers=headers_viewer,
    )
    assert res_v.status_code == 403

    # Owner resolves manually
    res_o = client.post(
        f"/api/v1/workspaces/{ws.id}/alerts/{alert.id}/resolve",
        json={"confirm": True},
        headers=headers_owner,
    )
    assert res_o.status_code == 200
    assert res_o.json()["status"] == "RESOLVED"

    # Verify audit event was logged
    events = db_session.query(AlertEvent).filter(AlertEvent.alert_id == alert.id).all()
    assert any("manual" in e.message.lower() for e in events)


def test_security_secret_redaction_in_alerts(test_setup: dict, db_session: Session):
    owner = test_setup["owner"]
    ws = test_setup["workspace"]
    server = test_setup["server"]

    rule = AlertRule(
        workspace_id=ws.id,
        name="Deployment Failure Rule",
        metric_type="DEPLOYMENT_STATUS",
        operator="EQUAL",
        threshold=0.0,
        duration_seconds=0,
        severity="CRITICAL",
        server_id=server.id,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()

    eval_service = AlertEvaluationService(db_session)

    # Telemetry containing fake credentials in message
    sensitive_message = "Deployment failed: SSH auth failed with password=super_secret_123 and token=ghp_abc123"
    redacted = eval_service.redactor.redact(sensitive_message)

    assert "super_secret_123" not in redacted
    assert "ghp_abc123" not in redacted
    assert "********" in redacted
