from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, RequireWorkspaceRole
from app.models.user import User
from app.models.workspace_member import WorkspaceRole
from app.models.alert import (
    AlertRule,
    Alert,
    AlertEvent,
    NotificationPreference,
    Notification,
)
from app.models.environment import Environment
from app.models.server import Server
from app.schemas.alert import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertResponse,
    AlertDetailResponse,
    AlertEventResponse,
    AlertResolveRequest,
    NotificationResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    UnreadNotificationCountResponse,
    AlertEvaluationSummary,
)
from app.schemas.audit_log import AuditAction, AuditStatus
from app.services.alert_evaluation import AlertEvaluationService
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

router = APIRouter()


# -------------------------------------------------------------
# 1. ALERT RULES API
# -------------------------------------------------------------

@router.get(
    "/workspaces/{workspace_id}/alert-rules",
    response_model=List[AlertRuleResponse],
    summary="List all alert rules for a workspace",
)
def list_alert_rules(
    workspace_id: UUID,
    environment_id: Optional[UUID] = Query(None),
    server_id: Optional[UUID] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    query = db.query(AlertRule).filter(AlertRule.workspace_id == workspace_id)
    if environment_id:
        query = query.filter(AlertRule.environment_id == environment_id)
    if server_id:
        query = query.filter(AlertRule.server_id == server_id)
    if is_enabled is not None:
        query = query.filter(AlertRule.is_enabled == is_enabled)

    rules = query.order_by(AlertRule.created_at.desc()).all()
    results = []
    for r in rules:
        resp = AlertRuleResponse.model_validate(r)
        if r.environment:
            resp.environment_name = r.environment.name
        if r.server:
            resp.server_name = r.server.name
        results.append(resp)
    return results


@router.post(
    "/workspaces/{workspace_id}/alert-rules",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert rule",
)
def create_alert_rule(
    workspace_id: UUID,
    payload: AlertRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
):
    if payload.environment_id:
        env = (
            db.query(Environment)
            .filter(
                Environment.id == payload.environment_id,
                Environment.workspace_id == workspace_id,
            )
            .first()
        )
        if not env:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment tidak ditemukan pada workspace ini.",
            )

    if payload.server_id:
        srv = (
            db.query(Server)
            .filter(
                Server.id == payload.server_id,
                Server.workspace_id == workspace_id,
            )
            .first()
        )
        if not srv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server tidak ditemukan pada workspace ini.",
            )

    rule = AlertRule(
        workspace_id=workspace_id,
        name=payload.name,
        description=payload.description,
        metric_type=payload.metric_type.value,
        operator=payload.operator.value,
        threshold=payload.threshold,
        target_identifier=payload.target_identifier,
        duration_seconds=payload.duration_seconds,
        severity=payload.severity.value,
        is_enabled=payload.is_enabled,
        environment_id=payload.environment_id,
        server_id=payload.server_id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    audit = AuditService(db)
    audit.log(
        action=AuditAction.ALERT_RULE_CREATED,
        resource_type="alert_rule",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace_id,
        user_id=current_user.id,
        resource_id=str(rule.id),
        environment_id=rule.environment_id,
        server_id=rule.server_id,
        metadata={"name": rule.name, "metric_type": rule.metric_type, "severity": rule.severity},
        request=request,
    )

    resp = AlertRuleResponse.model_validate(rule)
    if rule.environment:
        resp.environment_name = rule.environment.name
    if rule.server:
        resp.server_name = rule.server.name
    return resp


@router.get(
    "/workspaces/{workspace_id}/alert-rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Get alert rule details",
)
def get_alert_rule_detail(
    workspace_id: UUID,
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    rule = (
        db.query(AlertRule)
        .filter(
            AlertRule.id == rule_id,
            AlertRule.workspace_id == workspace_id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aturan alert tidak ditemukan.",
        )

    resp = AlertRuleResponse.model_validate(rule)
    if rule.environment:
        resp.environment_name = rule.environment.name
    if rule.server:
        resp.server_name = rule.server.name
    return resp


@router.patch(
    "/workspaces/{workspace_id}/alert-rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Update an alert rule",
)
def update_alert_rule(
    workspace_id: UUID,
    rule_id: UUID,
    payload: AlertRuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
):
    rule = (
        db.query(AlertRule)
        .filter(
            AlertRule.id == rule_id,
            AlertRule.workspace_id == workspace_id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aturan alert tidak ditemukan.",
        )

    if payload.environment_id is not None:
        if payload.environment_id:
            env = (
                db.query(Environment)
                .filter(
                    Environment.id == payload.environment_id,
                    Environment.workspace_id == workspace_id,
                )
                .first()
            )
            if not env:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Environment tidak ditemukan.",
                )
        rule.environment_id = payload.environment_id

    if payload.server_id is not None:
        if payload.server_id:
            srv = (
                db.query(Server)
                .filter(
                    Server.id == payload.server_id,
                    Server.workspace_id == workspace_id,
                )
                .first()
            )
            if not srv:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Server tidak ditemukan.",
                )
        rule.server_id = payload.server_id

    if payload.name is not None:
        rule.name = payload.name
    if payload.description is not None:
        rule.description = payload.description
    if payload.metric_type is not None:
        rule.metric_type = payload.metric_type.value
    if payload.operator is not None:
        rule.operator = payload.operator.value
    if payload.threshold is not None:
        rule.threshold = payload.threshold
    if payload.target_identifier is not None:
        rule.target_identifier = payload.target_identifier
    if payload.duration_seconds is not None:
        rule.duration_seconds = payload.duration_seconds
    if payload.severity is not None:
        rule.severity = payload.severity.value
    if payload.is_enabled is not None:
        rule.is_enabled = payload.is_enabled

    db.commit()
    db.refresh(rule)

    audit = AuditService(db)
    audit.log(
        action=AuditAction.ALERT_RULE_UPDATED,
        resource_type="alert_rule",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace_id,
        user_id=current_user.id,
        resource_id=str(rule.id),
        environment_id=rule.environment_id,
        server_id=rule.server_id,
        metadata={"name": rule.name},
        request=request,
    )

    resp = AlertRuleResponse.model_validate(rule)
    if rule.environment:
        resp.environment_name = rule.environment.name
    if rule.server:
        resp.server_name = rule.server.name
    return resp


@router.delete(
    "/workspaces/{workspace_id}/alert-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an alert rule",
)
def delete_alert_rule(
    workspace_id: UUID,
    rule_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
):
    rule = (
        db.query(AlertRule)
        .filter(
            AlertRule.id == rule_id,
            AlertRule.workspace_id == workspace_id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aturan alert tidak ditemukan.",
        )

    rule_name = rule.name
    env_id = rule.environment_id
    srv_id = rule.server_id
    db.delete(rule)
    db.commit()

    audit = AuditService(db)
    audit.log(
        action=AuditAction.ALERT_RULE_DELETED,
        resource_type="alert_rule",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace_id,
        user_id=current_user.id,
        resource_id=str(rule_id),
        environment_id=env_id,
        server_id=srv_id,
        metadata={"name": rule_name},
        request=request,
    )

    return None


# -------------------------------------------------------------
# 2. ALERTS (REALTIME & HISTORY) API
# -------------------------------------------------------------

@router.get(
    "/workspaces/{workspace_id}/alerts",
    response_model=List[AlertResponse],
    summary="List alerts with filters and pagination",
)
def list_alerts(
    workspace_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    server_id: Optional[UUID] = Query(None),
    environment_id: Optional[UUID] = Query(None),
    alert_rule_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    query = db.query(Alert).filter(Alert.workspace_id == workspace_id)
    if status_filter:
        query = query.filter(Alert.status == status_filter.upper())
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if server_id:
        query = query.filter(Alert.server_id == server_id)
    if environment_id:
        query = query.filter(Alert.environment_id == environment_id)
    if alert_rule_id:
        query = query.filter(Alert.alert_rule_id == alert_rule_id)

    alerts = (
        query.order_by(Alert.triggered_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for a in alerts:
        resp = AlertResponse.model_validate(a)
        if a.alert_rule:
            resp.alert_rule_name = a.alert_rule.name
        if a.environment:
            resp.environment_name = a.environment.name
        if a.server:
            resp.server_name = a.server.name
        results.append(resp)
    return results


@router.get(
    "/workspaces/{workspace_id}/alerts/{alert_id}",
    response_model=AlertDetailResponse,
    summary="Get alert detail including audit events",
)
def get_alert_detail(
    workspace_id: UUID,
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id,
            Alert.workspace_id == workspace_id,
        )
        .first()
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert tidak ditemukan.",
        )

    resp = AlertDetailResponse.model_validate(alert)
    if alert.alert_rule:
        resp.alert_rule_name = alert.alert_rule.name
    if alert.environment:
        resp.environment_name = alert.environment.name
    if alert.server:
        resp.server_name = alert.server.name

    resp.events = [
        AlertEventResponse.model_validate(e)
        for e in sorted(alert.events, key=lambda x: x.created_at)
    ]
    return resp


@router.get(
    "/workspaces/{workspace_id}/alerts/{alert_id}/events",
    response_model=List[AlertEventResponse],
    summary="Get audit events for an alert",
)
def get_alert_events(
    workspace_id: UUID,
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id,
            Alert.workspace_id == workspace_id,
        )
        .first()
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert tidak ditemukan.",
        )

    events = (
        db.query(AlertEvent)
        .filter(AlertEvent.alert_id == alert_id)
        .order_by(AlertEvent.created_at.asc())
        .all()
    )
    return [AlertEventResponse.model_validate(e) for e in events]


@router.post(
    "/workspaces/{workspace_id}/alerts/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Manually resolve an active alert",
)
async def resolve_alert_manually(
    workspace_id: UUID,
    alert_id: UUID,
    payload: AlertResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
):
    eval_service = AlertEvaluationService(db)
    resolved_alert = await eval_service.resolve_alert_manually(
        alert_id=alert_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        confirm=payload.confirm,
    )
    resp = AlertResponse.model_validate(resolved_alert)
    if resolved_alert.alert_rule:
        resp.alert_rule_name = resolved_alert.alert_rule.name
    if resolved_alert.environment:
        resp.environment_name = resolved_alert.environment.name
    if resolved_alert.server:
        resp.server_name = resolved_alert.server.name
    return resp


@router.post(
    "/workspaces/{workspace_id}/alerts/evaluate",
    response_model=AlertEvaluationSummary,
    summary="Trigger alert evaluation cycle for a workspace",
)
async def evaluate_workspace_alerts(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    eval_service = AlertEvaluationService(db)
    res = await eval_service.evaluate_workspace_rules(workspace_id=workspace_id)
    return AlertEvaluationSummary(**res)


# -------------------------------------------------------------
# 3. IN-APP NOTIFICATIONS & PREFERENCES API
# -------------------------------------------------------------

@router.get(
    "/workspaces/{workspace_id}/notifications",
    response_model=List[NotificationResponse],
    summary="Get user in-app notifications in workspace",
)
def get_user_notifications(
    workspace_id: UUID,
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    notif_service = NotificationService(db)
    notifs = notif_service.get_user_notifications(
        user_id=current_user.id,
        workspace_id=workspace_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return [NotificationResponse.model_validate(n) for n in notifs]


@router.get(
    "/workspaces/{workspace_id}/notifications/unread-count",
    response_model=UnreadNotificationCountResponse,
    summary="Get count of unread notifications for current user",
)
def get_unread_notification_count(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    notif_service = NotificationService(db)
    count = notif_service.get_unread_count(current_user.id, workspace_id)
    return UnreadNotificationCountResponse(
        workspace_id=workspace_id, unread_count=count
    )


@router.patch(
    "/workspaces/{workspace_id}/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a specific notification as read",
)
def mark_notification_as_read(
    workspace_id: UUID,
    notification_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    notif_service = NotificationService(db)
    notif = notif_service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id,
        workspace_id=workspace_id,
    )

    audit = AuditService(db)
    audit.log(
        action=AuditAction.NOTIFICATION_READ,
        resource_type="notification",
        status=AuditStatus.SUCCESS,
        workspace_id=workspace_id,
        user_id=current_user.id,
        resource_id=str(notification_id),
        metadata={"notification_id": str(notification_id)},
        request=request,
    )

    return NotificationResponse.model_validate(notif)


@router.post(
    "/workspaces/{workspace_id}/notifications/mark-all-read",
    summary="Mark all notifications as read for current user",
)
def mark_all_notifications_as_read(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    notif_service = NotificationService(db)
    updated = notif_service.mark_all_as_read(current_user.id, workspace_id)
    return {"message": "Seluruh notifikasi ditandai telah dibaca.", "updated_count": updated}


@router.get(
    "/workspaces/{workspace_id}/notification-preferences",
    response_model=NotificationPreferenceResponse,
    summary="Get user notification preferences in workspace",
)
def get_notification_preferences(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    notif_service = NotificationService(db)
    pref = notif_service.get_or_create_preference(current_user.id, workspace_id)
    return NotificationPreferenceResponse.model_validate(pref)


@router.patch(
    "/workspaces/{workspace_id}/notification-preferences",
    response_model=NotificationPreferenceResponse,
    summary="Update user notification preferences in workspace",
)
def update_notification_preferences(
    workspace_id: UUID,
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(
        RequireWorkspaceRole(
            [
                WorkspaceRole.OWNER,
                WorkspaceRole.ADMIN,
                WorkspaceRole.DEVELOPER,
                WorkspaceRole.VIEWER,
            ]
        )
    ),
):
    notif_service = NotificationService(db)
    pref = notif_service.update_preference(
        user_id=current_user.id,
        workspace_id=workspace_id,
        in_app_enabled=payload.in_app_enabled,
        email_enabled=payload.email_enabled,
        minimum_severity=payload.minimum_severity.value if payload.minimum_severity else None,
    )
    return NotificationPreferenceResponse.model_validate(pref)
