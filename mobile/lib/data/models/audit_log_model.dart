class AuditUserSummary {
  final String id;
  final String name;
  final String email;

  AuditUserSummary({
    required this.id,
    required this.name,
    required this.email,
  });

  factory AuditUserSummary.fromJson(Map<String, dynamic> json) {
    return AuditUserSummary(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      email: json['email'] ?? '',
    );
  }
}

class AuditLogModel {
  final String id;
  final String? workspaceId;
  final String? userId;
  final AuditUserSummary? user;
  final String action;
  final String resourceType;
  final String? resourceId;
  final String? environmentId;
  final String? serverId;
  final String status;
  final String? ipAddress;
  final String? userAgent;
  final Map<String, dynamic>? metadata;
  final DateTime createdAt;

  AuditLogModel({
    required this.id,
    this.workspaceId,
    this.userId,
    this.user,
    required this.action,
    required this.resourceType,
    this.resourceId,
    this.environmentId,
    this.serverId,
    required this.status,
    this.ipAddress,
    this.userAgent,
    this.metadata,
    required this.createdAt,
  });

  factory AuditLogModel.fromJson(Map<String, dynamic> json) {
    return AuditLogModel(
      id: json['id'] ?? '',
      workspaceId: json['workspace_id'],
      userId: json['user_id'],
      user: json['user'] != null ? AuditUserSummary.fromJson(json['user']) : null,
      action: json['action'] ?? '',
      resourceType: json['resource_type'] ?? '',
      resourceId: json['resource_id'],
      environmentId: json['environment_id'],
      serverId: json['server_id'],
      status: json['status'] ?? 'SUCCESS',
      ipAddress: json['ip_address'],
      userAgent: json['user_agent'],
      metadata: json['metadata'] != null ? Map<String, dynamic>.from(json['metadata']) : null,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class AuditLogListResponseModel {
  final List<AuditLogModel> items;
  final int total;
  final int limit;
  final int offset;

  AuditLogListResponseModel({
    required this.items,
    required this.total,
    required this.limit,
    required this.offset,
  });

  factory AuditLogListResponseModel.fromJson(Map<String, dynamic> json) {
    var rawItems = json['items'] as List? ?? [];
    List<AuditLogModel> parsedItems =
        rawItems.map((e) => AuditLogModel.fromJson(e)).toList();

    return AuditLogListResponseModel(
      items: parsedItems,
      total: json['total'] ?? 0,
      limit: json['limit'] ?? 50,
      offset: json['offset'] ?? 0,
    );
  }
}
