class AgentModel {
  final String id;
  final String serverId;
  final String workspaceId;
  final String name;
  final String agentVersion;
  final String status;
  final DateTime? lastSeenAt;
  final DateTime? connectedAt;
  final DateTime? disconnectedAt;
  final String? hostname;
  final String? operatingSystem;
  final String? architecture;
  final Map<String, dynamic> capabilities;
  final bool isActive;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  AgentModel({
    required this.id,
    required this.serverId,
    required this.workspaceId,
    required this.name,
    this.agentVersion = '1.0.0',
    this.status = 'PENDING',
    this.lastSeenAt,
    this.connectedAt,
    this.disconnectedAt,
    this.hostname,
    this.operatingSystem,
    this.architecture,
    this.capabilities = const {},
    this.isActive = true,
    this.createdAt,
    this.updatedAt,
  });

  bool get isOnline => status == 'ONLINE';
  bool get isOffline => status == 'OFFLINE';
  bool get isDisabled => status == 'DISABLED';

  bool hasCapability(String key) {
    final val = capabilities[key];
    if (val is bool) return val;
    return val != null;
  }

  factory AgentModel.fromJson(Map<String, dynamic> json) {
    return AgentModel(
      id: json['id']?.toString() ?? '',
      serverId: json['server_id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      agentVersion: json['agent_version'] as String? ?? '1.0.0',
      status: json['status'] as String? ?? 'PENDING',
      lastSeenAt: json['last_seen_at'] != null ? DateTime.tryParse(json['last_seen_at'].toString()) : null,
      connectedAt: json['connected_at'] != null ? DateTime.tryParse(json['connected_at'].toString()) : null,
      disconnectedAt: json['disconnected_at'] != null ? DateTime.tryParse(json['disconnected_at'].toString()) : null,
      hostname: json['hostname'] as String?,
      operatingSystem: json['operating_system'] as String?,
      architecture: json['architecture'] as String?,
      capabilities: json['capabilities'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(json['capabilities'] as Map)
          : const {},
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'server_id': serverId,
      'workspace_id': workspaceId,
      'name': name,
      'agent_version': agentVersion,
      'status': status,
      'last_seen_at': lastSeenAt?.toIso8601String(),
      'connected_at': connectedAt?.toIso8601String(),
      'disconnected_at': disconnectedAt?.toIso8601String(),
      'hostname': hostname,
      'operating_system': operatingSystem,
      'architecture': architecture,
      'capabilities': capabilities,
      'is_active': isActive,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}

class AgentEnrollmentResponseModel {
  final String enrollmentToken;
  final String serverId;
  final String workspaceId;
  final DateTime expiresAt;
  final String installerCommand;

  AgentEnrollmentResponseModel({
    required this.enrollmentToken,
    required this.serverId,
    required this.workspaceId,
    required this.expiresAt,
    required this.installerCommand,
  });

  factory AgentEnrollmentResponseModel.fromJson(Map<String, dynamic> json) {
    return AgentEnrollmentResponseModel(
      enrollmentToken: json['enrollment_token'] as String? ?? '',
      serverId: json['server_id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      expiresAt: json['expires_at'] != null
          ? DateTime.tryParse(json['expires_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      installerCommand: json['installer_command'] as String? ?? '',
    );
  }
}

class AgentJobModel {
  final String id;
  final String agentId;
  final String workspaceId;
  final String serverId;
  final String operation;
  final String status;
  final String? requestId;
  final Map<String, dynamic>? payload;
  final Map<String, dynamic>? result;
  final String? errorCategory;
  final String? errorMessage;
  final int timeoutSeconds;
  final DateTime createdAt;
  final DateTime? startedAt;
  final DateTime? finishedAt;
  final DateTime expiresAt;

  AgentJobModel({
    required this.id,
    required this.agentId,
    required this.workspaceId,
    required this.serverId,
    required this.operation,
    required this.status,
    this.requestId,
    this.payload,
    this.result,
    this.errorCategory,
    this.errorMessage,
    required this.timeoutSeconds,
    required this.createdAt,
    this.startedAt,
    this.finishedAt,
    required this.expiresAt,
  });

  factory AgentJobModel.fromJson(Map<String, dynamic> json) {
    return AgentJobModel(
      id: json['id']?.toString() ?? '',
      agentId: json['agent_id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      serverId: json['server_id']?.toString() ?? '',
      operation: json['operation'] as String? ?? '',
      status: json['status'] as String? ?? 'PENDING',
      requestId: json['request_id'] as String?,
      payload: json['payload'] is Map<String, dynamic> ? Map<String, dynamic>.from(json['payload'] as Map) : null,
      result: json['result'] is Map<String, dynamic> ? Map<String, dynamic>.from(json['result'] as Map) : null,
      errorCategory: json['error_category'] as String?,
      errorMessage: json['error_message'] as String?,
      timeoutSeconds: json['timeout_seconds'] as int? ?? 30,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now() : DateTime.now(),
      startedAt: json['started_at'] != null ? DateTime.tryParse(json['started_at'].toString()) : null,
      finishedAt: json['finished_at'] != null ? DateTime.tryParse(json['finished_at'].toString()) : null,
      expiresAt: json['expires_at'] != null ? DateTime.tryParse(json['expires_at'].toString()) ?? DateTime.now() : DateTime.now(),
    );
  }
}
