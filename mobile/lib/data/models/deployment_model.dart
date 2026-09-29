class DeploymentConfigModel {
  final String id;
  final String workspaceId;
  final String environmentId;
  final String serverId;
  final String name;
  final String? description;
  final String applicationName;
  final String workingDirectory;
  final String deploymentType; // "SYSTEMD" or "DOCKER_COMPOSE"
  final String? branch;
  final String? repositoryUrl;
  final String? restartServiceName;
  final String? composeProjectName;
  final String? healthCheckType;
  final String? healthCheckUrl;
  final bool isActive;
  final String? environmentName;
  final bool environmentIsProtected;
  final String? serverName;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  DeploymentConfigModel({
    required this.id,
    required this.workspaceId,
    required this.environmentId,
    required this.serverId,
    required this.name,
    this.description,
    required this.applicationName,
    required this.workingDirectory,
    this.deploymentType = 'SYSTEMD',
    this.branch,
    this.repositoryUrl,
    this.restartServiceName,
    this.composeProjectName,
    this.healthCheckType,
    this.healthCheckUrl,
    this.isActive = true,
    this.environmentName,
    this.environmentIsProtected = false,
    this.serverName,
    this.createdAt,
    this.updatedAt,
  });

  bool get isDockerCompose => deploymentType.toUpperCase() == 'DOCKER_COMPOSE';
  bool get isSystemd => deploymentType.toUpperCase() == 'SYSTEMD';

  factory DeploymentConfigModel.fromJson(Map<String, dynamic> json) {
    return DeploymentConfigModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      environmentId: json['environment_id']?.toString() ?? '',
      serverId: json['server_id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      description: json['description'] as String?,
      applicationName: json['application_name']?.toString() ?? '',
      workingDirectory: json['working_directory']?.toString() ?? '',
      deploymentType: json['deployment_type']?.toString() ?? 'SYSTEMD',
      branch: json['branch'] as String?,
      repositoryUrl: json['repository_url'] as String?,
      restartServiceName: json['restart_service_name'] as String?,
      composeProjectName: json['compose_project_name'] as String?,
      healthCheckType: json['health_check_type'] as String?,
      healthCheckUrl: json['health_check_url'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      environmentName: json['environment_name'] as String?,
      environmentIsProtected: json['environment_is_protected'] as bool? ?? false,
      serverName: json['server_name'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())?.toLocal()
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'].toString())?.toLocal()
          : null,
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
      'application_name': applicationName,
      'working_directory': workingDirectory,
      'deployment_type': deploymentType,
      'branch': branch,
      'repository_url': repositoryUrl,
      'restart_service_name': restartServiceName,
      'compose_project_name': composeProjectName,
      'health_check_type': healthCheckType,
      'health_check_url': healthCheckUrl,
      'is_active': isActive,
      'environment_name': environmentName,
      'environment_is_protected': environmentIsProtected,
      'server_name': serverName,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}

class DeploymentModel {
  final String id;
  final String workspaceId;
  final String environmentId;
  final String serverId;
  final String deploymentConfigId;
  final String status; // "PENDING", "RUNNING", "SUCCESS", "FAILED", "CANCELLED"
  final String? triggeredByUserId;
  final String? triggeredByName;
  final DateTime? startedAt;
  final DateTime? finishedAt;
  final String? commitReference;
  final String? message;
  final String? errorMessage;
  final String? deploymentConfigName;
  final String? environmentName;
  final bool environmentIsProtected;
  final String? serverName;
  final DateTime? createdAt;

  DeploymentModel({
    required this.id,
    required this.workspaceId,
    required this.environmentId,
    required this.serverId,
    required this.deploymentConfigId,
    required this.status,
    this.triggeredByUserId,
    this.triggeredByName,
    this.startedAt,
    this.finishedAt,
    this.commitReference,
    this.message,
    this.errorMessage,
    this.deploymentConfigName,
    this.environmentName,
    this.environmentIsProtected = false,
    this.serverName,
    this.createdAt,
  });

  bool get isRunning => status.toUpperCase() == 'RUNNING';
  bool get isSuccess => status.toUpperCase() == 'SUCCESS';
  bool get isFailed => status.toUpperCase() == 'FAILED';
  bool get isPending => status.toUpperCase() == 'PENDING';

  factory DeploymentModel.fromJson(Map<String, dynamic> json) {
    return DeploymentModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      environmentId: json['environment_id']?.toString() ?? '',
      serverId: json['server_id']?.toString() ?? '',
      deploymentConfigId: json['deployment_config_id']?.toString() ?? '',
      status: json['status']?.toString() ?? 'PENDING',
      triggeredByUserId: json['triggered_by_user_id'] as String?,
      triggeredByName: json['triggered_by_name'] as String?,
      startedAt: json['started_at'] != null
          ? DateTime.tryParse(json['started_at'].toString())?.toLocal()
          : null,
      finishedAt: json['finished_at'] != null
          ? DateTime.tryParse(json['finished_at'].toString())?.toLocal()
          : null,
      commitReference: json['commit_reference'] as String?,
      message: json['message'] as String?,
      errorMessage: json['error_message'] as String?,
      deploymentConfigName: json['deployment_config_name'] as String?,
      environmentName: json['environment_name'] as String?,
      environmentIsProtected: json['environment_is_protected'] as bool? ?? false,
      serverName: json['server_name'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())?.toLocal()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'workspace_id': workspaceId,
      'environment_id': environmentId,
      'server_id': serverId,
      'deployment_config_id': deploymentConfigId,
      'status': status,
      'triggered_by_user_id': triggeredByUserId,
      'triggered_by_name': triggeredByName,
      'started_at': startedAt?.toIso8601String(),
      'finished_at': finishedAt?.toIso8601String(),
      'commit_reference': commitReference,
      'message': message,
      'error_message': errorMessage,
      'deployment_config_name': deploymentConfigName,
      'environment_name': environmentName,
      'environment_is_protected': environmentIsProtected,
      'server_name': serverName,
      'created_at': createdAt?.toIso8601String(),
    };
  }
}

class DeploymentLogEntryModel {
  final int sequence;
  final DateTime? timestamp;
  final String level; // "INFO", "WARNING", "ERROR"
  final String message;

  DeploymentLogEntryModel({
    required this.sequence,
    this.timestamp,
    required this.level,
    required this.message,
  });

  bool get isError => level.toUpperCase() == 'ERROR';
  bool get isWarning => level.toUpperCase() == 'WARNING';
  bool get isInfo => level.toUpperCase() == 'INFO';

  factory DeploymentLogEntryModel.fromJson(Map<String, dynamic> json) {
    return DeploymentLogEntryModel(
      sequence: json['sequence'] as int? ?? 0,
      timestamp: json['timestamp'] != null
          ? DateTime.tryParse(json['timestamp'].toString())?.toLocal()
          : null,
      level: json['level']?.toString() ?? 'INFO',
      message: json['message']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'sequence': sequence,
      'timestamp': timestamp?.toIso8601String(),
      'level': level,
      'message': message,
    };
  }
}

class DeploymentLogsModel {
  final String deploymentId;
  final String status;
  final int linesReturned;
  final List<DeploymentLogEntryModel> entries;

  DeploymentLogsModel({
    required this.deploymentId,
    required this.status,
    required this.linesReturned,
    this.entries = const [],
  });

  factory DeploymentLogsModel.fromJson(Map<String, dynamic> json) {
    return DeploymentLogsModel(
      deploymentId: json['deployment_id']?.toString() ?? '',
      status: json['status']?.toString() ?? 'PENDING',
      linesReturned: json['lines_returned'] as int? ?? 0,
      entries: (json['entries'] as List<dynamic>?)
              ?.map((e) => DeploymentLogEntryModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'deployment_id': deploymentId,
      'status': status,
      'lines_returned': linesReturned,
      'entries': entries.map((e) => e.toJson()).toList(),
    };
  }
}
