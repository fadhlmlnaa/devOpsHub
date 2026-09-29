class WorkspaceMemberModel {
  final String id;
  final String userId;
  final String role;
  final String? userEmail;
  final String? userName;
  final DateTime? createdAt;

  WorkspaceMemberModel({
    required this.id,
    required this.userId,
    required this.role,
    this.userEmail,
    this.userName,
    this.createdAt,
  });

  factory WorkspaceMemberModel.fromJson(Map<String, dynamic> json) {
    return WorkspaceMemberModel(
      id: json['id']?.toString() ?? '',
      userId: json['user_id']?.toString() ?? '',
      role: json['role'] as String? ?? 'VIEWER',
      userEmail: json['user_email'] as String?,
      userName: json['user_name'] as String?,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'role': role,
      'user_email': userEmail,
      'user_name': userName,
      'created_at': createdAt?.toIso8601String(),
    };
  }
}
