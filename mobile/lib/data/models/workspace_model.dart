class WorkspaceModel {
  final String id;
  final String name;
  final String? description;
  final String timezone;
  final String role;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  WorkspaceModel({
    required this.id,
    required this.name,
    this.description,
    this.timezone = 'UTC',
    this.role = 'MEMBER',
    this.createdAt,
    this.updatedAt,
  });

  factory WorkspaceModel.fromJson(Map<String, dynamic> json) {
    return WorkspaceModel(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      timezone: json['timezone'] as String? ?? 'UTC',
      role: json['role'] as String? ?? 'MEMBER',
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'timezone': timezone,
      'role': role,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}
