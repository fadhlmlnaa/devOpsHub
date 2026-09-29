import 'environment_model.dart';

class ServerModel {
  final String id;
  final String workspaceId;
  final String environmentId;
  final String name;
  final String? hostname;
  final String? ipAddress;
  final int sshPort;
  final String? username;
  final String? operatingSystem;
  final String? description;
  final bool isActive;
  final EnvironmentModel? environment;
  final bool hasCredential;
  final String? authType;
  final String status;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  ServerModel({
    required this.id,
    required this.workspaceId,
    required this.environmentId,
    required this.name,
    this.hostname,
    this.ipAddress,
    this.sshPort = 22,
    this.username,
    this.operatingSystem,
    this.description,
    this.isActive = true,
    this.environment,
    this.hasCredential = false,
    this.authType,
    this.status = 'UNKNOWN',
    this.createdAt,
    this.updatedAt,
  });

  factory ServerModel.fromJson(Map<String, dynamic> json) {
    return ServerModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      environmentId: json['environment_id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      hostname: json['hostname'] as String?,
      ipAddress: json['ip_address'] as String?,
      sshPort: json['ssh_port'] is int ? json['ssh_port'] as int : int.tryParse(json['ssh_port']?.toString() ?? '22') ?? 22,
      username: json['username'] as String?,
      operatingSystem: json['operating_system'] as String?,
      description: json['description'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      environment: json['environment'] != null && json['environment'] is Map<String, dynamic>
          ? EnvironmentModel(
              id: json['environment']['id']?.toString() ?? '',
              workspaceId: json['workspace_id']?.toString() ?? '',
              name: json['environment']['name'] as String? ?? '',
              key: json['environment']['key'] as String? ?? '',
            )
          : null,
      hasCredential: json['has_credential'] as bool? ?? false,
      authType: json['auth_type'] as String?,
      status: json['status'] as String? ?? 'UNKNOWN',
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'workspace_id': workspaceId,
      'environment_id': environmentId,
      'name': name,
      'hostname': hostname,
      'ip_address': ipAddress,
      'ssh_port': sshPort,
      'username': username,
      'operating_system': operatingSystem,
      'description': description,
      'is_active': isActive,
      'has_credential': hasCredential,
      'auth_type': authType,
      'status': status,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}
