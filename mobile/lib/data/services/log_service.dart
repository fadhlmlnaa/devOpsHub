import '../models/log_model.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';

class LogService {
  final ApiClient apiClient;

  LogService({required this.apiClient});

  Future<LogResponseModel> getServiceLogs(
    String workspaceId,
    String serverId,
    String serviceName, {
    int lines = 100,
    String? since,
  }) async {
    if (workspaceId.trim().isEmpty || serverId.trim().isEmpty || serviceName.trim().isEmpty) {
      throw ApiException(message: 'Parameter request log tidak lengkap.');
    }

    final queryParams = <String, dynamic>{
      'lines': lines,
    };
    if (since != null && since.isNotEmpty && since != 'all') {
      queryParams['since'] = since;
    }

    final response = await apiClient.get(
      '/workspaces/$workspaceId/servers/$serverId/services/$serviceName/logs',
      queryParameters: queryParams,
    );

    if (response.data is Map<String, dynamic>) {
      return LogResponseModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format data response log tidak valid.');
  }
}
