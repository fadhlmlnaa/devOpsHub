class ConnectionTestModel {
  final bool success;
  final String message;
  final String status;
  final Map<String, dynamic>? serverInfo;

  ConnectionTestModel({
    required this.success,
    required this.message,
    required this.status,
    this.serverInfo,
  });

  factory ConnectionTestModel.fromJson(Map<String, dynamic> json) {
    return ConnectionTestModel(
      success: json['success'] as bool? ?? false,
      message: json['message'] as String? ?? '',
      status: json['status'] as String? ?? 'UNKNOWN',
      serverInfo: json['server_info'] is Map<String, dynamic> ? json['server_info'] as Map<String, dynamic> : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'message': message,
      'status': status,
      'server_info': serverInfo,
    };
  }
}
