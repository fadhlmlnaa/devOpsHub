class EnvironmentModel {
  final String id;
  final String workspaceId;
  final String name;
  final String key;
  final String? description;
  final int serverCount;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  EnvironmentModel({
    required this.id,
    required this.workspaceId,
    required this.name,
    required this.key,
    this.description,
    this.serverCount = 0,
    this.createdAt,
    this.updatedAt,
  });

  factory EnvironmentModel.fromJson(Map<String, dynamic> json) {
    return EnvironmentModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      key: json['key'] as String? ?? '',
      description: json['description'] as String?,
      serverCount: json['server_count'] is int ? json['server_count'] as int : int.tryParse(json['server_count']?.toString() ?? '0') ?? 0,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'workspace_id': workspaceId,
      'name': name,
      'key': key,
      'description': description,
      'server_count': serverCount,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}
