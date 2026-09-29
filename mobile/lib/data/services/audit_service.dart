import 'package:dio/dio.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../models/audit_log_model.dart';

class AuditService {
  final ApiClient apiClient;

  AuditService({required this.apiClient});

  Future<AuditLogListResponseModel> getWorkspaceAuditLogs(
    String workspaceId, {
    String? action,
    String? status,
    String? userId,
    String? resourceType,
    String? serverId,
    String? environmentId,
    DateTime? startDate,
    DateTime? endDate,
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/audit-logs',
        queryParameters: {
          if (action != null && action.isNotEmpty) 'action': action,
          if (status != null && status.isNotEmpty) 'status': status,
          if (userId != null && userId.isNotEmpty) 'user_id': userId,
          if (resourceType != null && resourceType.isNotEmpty) 'resource_type': resourceType,
          if (serverId != null && serverId.isNotEmpty) 'server_id': serverId,
          if (environmentId != null && environmentId.isNotEmpty) 'environment_id': environmentId,
          if (startDate != null) 'start_date': startDate.toIso8601String(),
          if (endDate != null) 'end_date': endDate.toIso8601String(),
          'limit': limit,
          'offset': offset,
        },
      );
      return AuditLogListResponseModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
