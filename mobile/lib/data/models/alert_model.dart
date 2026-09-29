class AlertRuleModel {
  final String id;
  final String workspaceId;
  final String? environmentId;
  final String? serverId;
  final String name;
  final String? description;
  final String metricType; // CPU_USAGE, MEMORY_USAGE, DISK_USAGE, LOAD_AVERAGE, SERVER_STATUS, SERVICE_STATUS, DEPLOYMENT_STATUS, BACKUP_STATUS
  final String operator; // GREATER_THAN, GREATER_THAN_OR_EQUAL, LESS_THAN, LESS_THAN_OR_EQUAL, EQUAL, NOT_EQUAL
  final double threshold;
  final int durationSeconds;
  final String severity; // INFO, WARNING, CRITICAL
  final String? targetIdentifier;
  final bool isEnabled;
  final String? environmentName;
  final String? serverName;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  AlertRuleModel({
    required this.id,
    required this.workspaceId,
    this.environmentId,
    this.serverId,
    required this.name,
    this.description,
    required this.metricType,
    required this.operator,
    required this.threshold,
    this.durationSeconds = 60,
    this.severity = 'WARNING',
    this.targetIdentifier,
    this.isEnabled = true,
    this.environmentName,
    this.serverName,
    this.createdAt,
    this.updatedAt,
  });

  String get metricTypeFormatted {
    switch (metricType.toUpperCase()) {
      case 'CPU_USAGE':
        return 'CPU Usage';
      case 'MEMORY_USAGE':
        return 'Memory Usage';
      case 'DISK_USAGE':
        return 'Disk Usage';
      case 'LOAD_AVERAGE':
        return 'Load Average';
      case 'SERVER_STATUS':
        return 'Server Status';
      case 'SERVICE_STATUS':
        return 'Service Status';
      case 'DEPLOYMENT_STATUS':
        return 'Deployment Status';
      case 'BACKUP_STATUS':
        return 'Backup Status';
      default:
        return metricType;
    }
  }

  String get operatorSymbol {
    switch (operator.toUpperCase()) {
      case 'GREATER_THAN':
        return '>';
      case 'GREATER_THAN_OR_EQUAL':
        return '>=';
      case 'LESS_THAN':
        return '<';
      case 'LESS_THAN_OR_EQUAL':
        return '<=';
      case 'EQUAL':
        return '==';
      case 'NOT_EQUAL':
        return '!=';
      default:
        return operator;
    }
  }

  String get conditionText {
    if (metricType.toUpperCase() == 'SERVER_STATUS') {
      return threshold == 0 ? '== OFFLINE' : '== ONLINE';
    }
    if (metricType.toUpperCase() == 'SERVICE_STATUS') {
      final svc = targetIdentifier?.isNotEmpty == true ? ' ($targetIdentifier)' : '';
      return '$svc ${threshold == 0 ? "== FAILED" : "== RUNNING"}';
    }
    if (metricType.toUpperCase() == 'DEPLOYMENT_STATUS') {
      return threshold == 0 ? '== FAILED' : '== SUCCESS';
    }
    if (metricType.toUpperCase() == 'BACKUP_STATUS') {
      return threshold == 0 ? '== FAILED' : '== SUCCESS';
    }
    final unit = (metricType.contains('USAGE')) ? '%' : '';
    return '$operatorSymbol ${threshold.toStringAsFixed(threshold.truncateToDouble() == threshold ? 0 : 1)}$unit';
  }

  String get durationFormatted {
    if (durationSeconds <= 0) return 'Seketika (0s)';
    if (durationSeconds < 60) return '${durationSeconds}s';
    final minutes = durationSeconds ~/ 60;
    final rem = durationSeconds % 60;
    if (rem == 0) return '$minutes mnt';
    return '$minutes mnt ${rem}s';
  }

  factory AlertRuleModel.fromJson(Map<String, dynamic> json) {
    return AlertRuleModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      environmentId: json['environment_id']?.toString(),
      serverId: json['server_id']?.toString(),
      name: json['name']?.toString() ?? '',
      description: json['description']?.toString(),
      metricType: json['metric_type']?.toString() ?? 'CPU_USAGE',
      operator: json['operator']?.toString() ?? 'GREATER_THAN',
      threshold: (json['threshold'] is num) ? (json['threshold'] as num).toDouble() : 0.0,
      durationSeconds: json['duration_seconds'] ?? 60,
      severity: json['severity']?.toString() ?? 'WARNING',
      targetIdentifier: json['target_identifier']?.toString(),
      isEnabled: json['is_enabled'] ?? true,
      environmentName: json['environment_name']?.toString(),
      serverName: json['server_name']?.toString(),
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'workspace_id': workspaceId,
      'environment_id': environmentId,
      'server_id': serverId,
      'name': name,
      'description': description,
      'metric_type': metricType,
      'operator': operator,
      'threshold': threshold,
      'duration_seconds': durationSeconds,
      'severity': severity,
      'target_identifier': targetIdentifier,
      'is_enabled': isEnabled,
    };
  }
}

class AlertEventModel {
  final String id;
  final String alertId;
  final String eventType; // TRIGGERED, NOTIFICATION_SENT, RESOLVED, NOTIFICATION_FAILED
  final String? message;
  final DateTime? createdAt;

  AlertEventModel({
    required this.id,
    required this.alertId,
    required this.eventType,
    this.message,
    this.createdAt,
  });

  factory AlertEventModel.fromJson(Map<String, dynamic> json) {
    return AlertEventModel(
      id: json['id']?.toString() ?? '',
      alertId: json['alert_id']?.toString() ?? '',
      eventType: json['event_type']?.toString() ?? 'TRIGGERED',
      message: json['message']?.toString(),
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'alert_id': alertId,
      'event_type': eventType,
      'message': message,
      'created_at': createdAt?.toIso8601String(),
    };
  }
}

class AlertModel {
  final String id;
  final String workspaceId;
  final String alertRuleId;
  final String? environmentId;
  final String? serverId;
  final String status; // FIRING, RESOLVED
  final String severity; // INFO, WARNING, CRITICAL
  final String title;
  final String? message;
  final double? currentValue;
  final double? thresholdValue;
  final DateTime? triggeredAt;
  final DateTime? resolvedAt;
  final DateTime? lastEvaluatedAt;
  final DateTime? notificationSentAt;
  final String? ruleName;
  final String? metricType;
  final String? serverName;
  final String? environmentName;
  final List<AlertEventModel>? events;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  AlertModel({
    required this.id,
    required this.workspaceId,
    required this.alertRuleId,
    this.environmentId,
    this.serverId,
    required this.status,
    required this.severity,
    required this.title,
    this.message,
    this.currentValue,
    this.thresholdValue,
    this.triggeredAt,
    this.resolvedAt,
    this.lastEvaluatedAt,
    this.notificationSentAt,
    this.ruleName,
    this.metricType,
    this.serverName,
    this.environmentName,
    this.events,
    this.createdAt,
    this.updatedAt,
  });

  bool get isFiring => status.toUpperCase() == 'FIRING';
  bool get isResolved => status.toUpperCase() == 'RESOLVED';
  bool get isCritical => severity.toUpperCase() == 'CRITICAL';
  bool get isWarning => severity.toUpperCase() == 'WARNING';
  bool get isInfo => severity.toUpperCase() == 'INFO';

  factory AlertModel.fromJson(Map<String, dynamic> json) {
    List<AlertEventModel>? parsedEvents;
    if (json['events'] != null && json['events'] is List) {
      parsedEvents = (json['events'] as List)
          .map((e) => AlertEventModel.fromJson(e as Map<String, dynamic>))
          .toList();
    }

    return AlertModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      alertRuleId: json['alert_rule_id']?.toString() ?? '',
      environmentId: json['environment_id']?.toString(),
      serverId: json['server_id']?.toString(),
      status: json['status']?.toString() ?? 'FIRING',
      severity: json['severity']?.toString() ?? 'WARNING',
      title: json['title']?.toString() ?? '',
      message: json['message']?.toString(),
      currentValue: (json['current_value'] is num) ? (json['current_value'] as num).toDouble() : null,
      thresholdValue: (json['threshold_value'] is num) ? (json['threshold_value'] as num).toDouble() : null,
      triggeredAt: json['triggered_at'] != null ? DateTime.tryParse(json['triggered_at']) : null,
      resolvedAt: json['resolved_at'] != null ? DateTime.tryParse(json['resolved_at']) : null,
      lastEvaluatedAt: json['last_evaluated_at'] != null ? DateTime.tryParse(json['last_evaluated_at']) : null,
      notificationSentAt: json['notification_sent_at'] != null ? DateTime.tryParse(json['notification_sent_at']) : null,
      ruleName: json['rule_name']?.toString(),
      metricType: json['metric_type']?.toString(),
      serverName: json['server_name']?.toString(),
      environmentName: json['environment_name']?.toString(),
      events: parsedEvents,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'workspace_id': workspaceId,
      'alert_rule_id': alertRuleId,
      'environment_id': environmentId,
      'server_id': serverId,
      'status': status,
      'severity': severity,
      'title': title,
      'message': message,
      'current_value': currentValue,
      'threshold_value': thresholdValue,
      'triggered_at': triggeredAt?.toIso8601String(),
      'resolved_at': resolvedAt?.toIso8601String(),
      'last_evaluated_at': lastEvaluatedAt?.toIso8601String(),
      'notification_sent_at': notificationSentAt?.toIso8601String(),
      'rule_name': ruleName,
      'metric_type': metricType,
      'server_name': serverName,
      'environment_name': environmentName,
      'events': events?.map((e) => e.toJson()).toList(),
    };
  }
}

class NotificationModel {
  final String id;
  final String userId;
  final String workspaceId;
  final String? alertId;
  final String title;
  final String message;
  final String severity; // INFO, WARNING, CRITICAL
  final bool isRead;
  final DateTime? createdAt;
  final DateTime? readAt;

  NotificationModel({
    required this.id,
    required this.userId,
    required this.workspaceId,
    this.alertId,
    required this.title,
    required this.message,
    this.severity = 'INFO',
    this.isRead = false,
    this.createdAt,
    this.readAt,
  });

  bool get isCritical => severity.toUpperCase() == 'CRITICAL';
  bool get isWarning => severity.toUpperCase() == 'WARNING';
  bool get isInfo => severity.toUpperCase() == 'INFO';

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id']?.toString() ?? '',
      userId: json['user_id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      alertId: json['alert_id']?.toString(),
      title: json['title']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      severity: json['severity']?.toString() ?? 'INFO',
      isRead: json['is_read'] ?? false,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
      readAt: json['read_at'] != null ? DateTime.tryParse(json['read_at']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'workspace_id': workspaceId,
      'alert_id': alertId,
      'title': title,
      'message': message,
      'severity': severity,
      'is_read': isRead,
      'created_at': createdAt?.toIso8601String(),
      'read_at': readAt?.toIso8601String(),
    };
  }
}

class NotificationPreferenceModel {
  final String id;
  final String userId;
  final String workspaceId;
  final bool inAppEnabled;
  final bool emailEnabled;
  final String minimumSeverity; // INFO, WARNING, CRITICAL
  final DateTime? createdAt;
  final DateTime? updatedAt;

  NotificationPreferenceModel({
    required this.id,
    required this.userId,
    required this.workspaceId,
    this.inAppEnabled = true,
    this.emailEnabled = false,
    this.minimumSeverity = 'INFO',
    this.createdAt,
    this.updatedAt,
  });

  factory NotificationPreferenceModel.fromJson(Map<String, dynamic> json) {
    return NotificationPreferenceModel(
      id: json['id']?.toString() ?? '',
      userId: json['user_id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      inAppEnabled: json['in_app_enabled'] ?? true,
      emailEnabled: json['email_enabled'] ?? false,
      minimumSeverity: json['minimum_severity']?.toString() ?? 'INFO',
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'workspace_id': workspaceId,
      'in_app_enabled': inAppEnabled,
      'email_enabled': emailEnabled,
      'minimum_severity': minimumSeverity,
    };
  }
}

class UnreadNotificationCountModel {
  final int unreadCount;

  UnreadNotificationCountModel({required this.unreadCount});

  factory UnreadNotificationCountModel.fromJson(Map<String, dynamic> json) {
    return UnreadNotificationCountModel(
      unreadCount: json['unread_count'] ?? 0,
    );
  }
}
