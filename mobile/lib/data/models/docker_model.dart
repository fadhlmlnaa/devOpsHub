import 'log_model.dart';

class DockerStatusModel {
  final String serverId;
  final bool installed;
  final bool running;
  final String? version;
  final String state; // NOT_INSTALLED, STOPPED, RUNNING, UNKNOWN
  final DateTime? checkedAt;

  DockerStatusModel({
    required this.serverId,
    required this.installed,
    required this.running,
    this.version,
    required this.state,
    this.checkedAt,
  });

  bool get isRunning => state.toUpperCase() == 'RUNNING';
  bool get isStopped => state.toUpperCase() == 'STOPPED';
  bool get isNotInstalled => state.toUpperCase() == 'NOT_INSTALLED';

  factory DockerStatusModel.fromJson(Map<String, dynamic> json) {
    return DockerStatusModel(
      serverId: json['server_id']?.toString() ?? '',
      installed: json['installed'] as bool? ?? false,
      running: json['running'] as bool? ?? false,
      version: json['version'] as String?,
      state: json['state']?.toString() ?? 'UNKNOWN',
      checkedAt: json['checked_at'] != null
          ? DateTime.tryParse(json['checked_at'].toString())?.toLocal()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'server_id': serverId,
      'installed': installed,
      'running': running,
      'version': version,
      'state': state,
      'checked_at': checkedAt?.toIso8601String(),
    };
  }
}

class DockerContainerModel {
  final String id;
  final String name;
  final String image;
  final String status;
  final String state; // running, exited, stopped, etc.
  final String? createdAt;
  final List<String> ports;

  DockerContainerModel({
    required this.id,
    required this.name,
    required this.image,
    required this.status,
    required this.state,
    this.createdAt,
    this.ports = const [],
  });

  bool get isRunning => state.toLowerCase() == 'running';
  bool get isStopped => state.toLowerCase() == 'exited' || state.toLowerCase() == 'stopped';

  factory DockerContainerModel.fromJson(Map<String, dynamic> json) {
    return DockerContainerModel(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      image: json['image']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      state: json['state']?.toString() ?? 'unknown',
      createdAt: json['created_at'] as String?,
      ports: (json['ports'] as List<dynamic>?)?.map((p) => p.toString()).toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'image': image,
      'status': status,
      'state': state,
      'created_at': createdAt,
      'ports': ports,
    };
  }
}

class DockerContainerDetailModel {
  final String id;
  final String name;
  final String image;
  final String state;
  final String status;
  final String? createdAt;
  final String? startedAt;
  final List<String> ports;
  final String? restartPolicy;
  final String? cpuUsage;
  final String? memoryUsage;
  final DateTime? checkedAt;

  DockerContainerDetailModel({
    required this.id,
    required this.name,
    required this.image,
    required this.state,
    required this.status,
    this.createdAt,
    this.startedAt,
    this.ports = const [],
    this.restartPolicy,
    this.cpuUsage,
    this.memoryUsage,
    this.checkedAt,
  });

  bool get isRunning => state.toLowerCase() == 'running';

  factory DockerContainerDetailModel.fromJson(Map<String, dynamic> json) {
    return DockerContainerDetailModel(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      image: json['image']?.toString() ?? '',
      state: json['state']?.toString() ?? 'unknown',
      status: json['status']?.toString() ?? '',
      createdAt: json['created_at'] as String?,
      startedAt: json['started_at'] as String?,
      ports: (json['ports'] as List<dynamic>?)?.map((p) => p.toString()).toList() ?? [],
      restartPolicy: json['restart_policy'] as String?,
      cpuUsage: json['cpu_usage'] as String?,
      memoryUsage: json['memory_usage'] as String?,
      checkedAt: json['checked_at'] != null
          ? DateTime.tryParse(json['checked_at'].toString())?.toLocal()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'image': image,
      'state': state,
      'status': status,
      'created_at': createdAt,
      'started_at': startedAt,
      'ports': ports,
      'restart_policy': restartPolicy,
      'cpu_usage': cpuUsage,
      'memory_usage': memoryUsage,
      'checked_at': checkedAt?.toIso8601String(),
    };
  }
}

class DockerContainerActionResultModel {
  final bool success;
  final String container;
  final String action;
  final String currentState;
  final String message;
  final DateTime? checkedAt;

  DockerContainerActionResultModel({
    required this.success,
    required this.container,
    required this.action,
    required this.currentState,
    required this.message,
    this.checkedAt,
  });

  factory DockerContainerActionResultModel.fromJson(Map<String, dynamic> json) {
    return DockerContainerActionResultModel(
      success: json['success'] as bool? ?? false,
      container: json['container']?.toString() ?? '',
      action: json['action']?.toString() ?? '',
      currentState: json['current_state']?.toString() ?? 'unknown',
      message: json['message']?.toString() ?? '',
      checkedAt: json['checked_at'] != null
          ? DateTime.tryParse(json['checked_at'].toString())?.toLocal()
          : null,
    );
  }
}

class DockerContainerLogsModel {
  final String container;
  final int linesRequested;
  final int linesReturned;
  final List<LogEntryModel> entries;
  final bool truncated;
  final DateTime? checkedAt;

  DockerContainerLogsModel({
    required this.container,
    required this.linesRequested,
    required this.linesReturned,
    this.entries = const [],
    required this.truncated,
    this.checkedAt,
  });

  factory DockerContainerLogsModel.fromJson(Map<String, dynamic> json) {
    return DockerContainerLogsModel(
      container: json['container']?.toString() ?? '',
      linesRequested: json['lines_requested'] as int? ?? 100,
      linesReturned: json['lines_returned'] as int? ?? 0,
      entries: (json['entries'] as List<dynamic>?)
              ?.map((e) => LogEntryModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      truncated: json['truncated'] as bool? ?? false,
      checkedAt: json['checked_at'] != null
          ? DateTime.tryParse(json['checked_at'].toString())?.toLocal()
          : null,
    );
  }
}

class DockerComposeProjectModel {
  final String id;
  final String workspaceId;
  final String serverId;
  final String environmentId;
  final String name;
  final String projectName;
  final String workingDirectory;
  final String composeFile;
  final String? description;
  final bool isActive;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  DockerComposeProjectModel({
    required this.id,
    required this.workspaceId,
    required this.serverId,
    required this.environmentId,
    required this.name,
    required this.projectName,
    required this.workingDirectory,
    required this.composeFile,
    this.description,
    required this.isActive,
    this.createdAt,
    this.updatedAt,
  });

  factory DockerComposeProjectModel.fromJson(Map<String, dynamic> json) {
    return DockerComposeProjectModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      serverId: json['server_id']?.toString() ?? '',
      environmentId: json['environment_id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      projectName: json['project_name']?.toString() ?? '',
      workingDirectory: json['working_directory']?.toString() ?? '',
      composeFile: json['compose_file']?.toString() ?? 'docker-compose.yml',
      description: json['description'] as String?,
      isActive: json['is_active'] as bool? ?? true,
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
      'server_id': serverId,
      'environment_id': environmentId,
      'name': name,
      'project_name': projectName,
      'working_directory': workingDirectory,
      'compose_file': composeFile,
      'description': description,
      'is_active': isActive,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}

class DockerComposeServiceStatusModel {
  final String name;
  final String? service;
  final String state;
  final String? status;

  DockerComposeServiceStatusModel({
    required this.name,
    this.service,
    required this.state,
    this.status,
  });

  bool get isRunning => state.toLowerCase() == 'running';

  factory DockerComposeServiceStatusModel.fromJson(Map<String, dynamic> json) {
    return DockerComposeServiceStatusModel(
      name: json['name']?.toString() ?? '',
      service: json['service'] as String?,
      state: json['state']?.toString() ?? 'unknown',
      status: json['status'] as String?,
    );
  }
}

class DockerComposeStatusModel {
  final String projectId;
  final String projectName;
  final String status; // RUNNING, STOPPED, PARTIAL, FAILED, UNKNOWN
  final List<DockerComposeServiceStatusModel> services;
  final DateTime? checkedAt;

  DockerComposeStatusModel({
    required this.projectId,
    required this.projectName,
    required this.status,
    this.services = const [],
    this.checkedAt,
  });

  bool get isRunning => status.toUpperCase() == 'RUNNING';
  bool get isPartial => status.toUpperCase() == 'PARTIAL';
  bool get isStopped => status.toUpperCase() == 'STOPPED';

  factory DockerComposeStatusModel.fromJson(Map<String, dynamic> json) {
    return DockerComposeStatusModel(
      projectId: json['project_id']?.toString() ?? '',
      projectName: json['project_name']?.toString() ?? '',
      status: json['status']?.toString() ?? 'UNKNOWN',
      services: (json['services'] as List<dynamic>?)
              ?.map((s) => DockerComposeServiceStatusModel.fromJson(s as Map<String, dynamic>))
              .toList() ??
          [],
      checkedAt: json['checked_at'] != null
          ? DateTime.tryParse(json['checked_at'].toString())?.toLocal()
          : null,
    );
  }
}

class DockerComposeActionResultModel {
  final bool success;
  final String projectId;
  final String action;
  final String status;
  final String message;
  final DateTime? checkedAt;

  DockerComposeActionResultModel({
    required this.success,
    required this.projectId,
    required this.action,
    required this.status,
    required this.message,
    this.checkedAt,
  });

  factory DockerComposeActionResultModel.fromJson(Map<String, dynamic> json) {
    return DockerComposeActionResultModel(
      success: json['success'] as bool? ?? false,
      projectId: json['project_id']?.toString() ?? '',
      action: json['action']?.toString() ?? '',
      status: json['status']?.toString() ?? 'UNKNOWN',
      message: json['message']?.toString() ?? '',
      checkedAt: json['checked_at'] != null
          ? DateTime.tryParse(json['checked_at'].toString())?.toLocal()
          : null,
    );
  }
}
