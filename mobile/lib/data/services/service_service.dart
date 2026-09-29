import '../models/service_model.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';

class ServiceService {
  final ApiClient apiClient;

  ServiceService({required this.apiClient});

  Future<ServiceListModel> getServices(
    String workspaceId,
    String serverId, {
    String? state,
    int limit = 100,
  }) async {
    if (workspaceId.trim().isEmpty || serverId.trim().isEmpty) {
      throw ApiException(message: 'ID Workspace atau Server tidak valid.');
    }

    final queryParams = <String, dynamic>{
      'limit': limit,
    };
    if (state != null && state.isNotEmpty && state != 'all') {
      queryParams['state'] = state;
    }

    final response = await apiClient.get(
      '/workspaces/$workspaceId/servers/$serverId/services',
      queryParameters: queryParams,
    );

    if (response.data is Map<String, dynamic>) {
      return ServiceListModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format data service tidak valid.');
  }

  Future<ServiceModel> getService(
    String workspaceId,
    String serverId,
    String serviceName,
  ) async {
    if (workspaceId.trim().isEmpty || serverId.trim().isEmpty || serviceName.trim().isEmpty) {
      throw ApiException(message: 'Parameter request service tidak lengkap.');
    }

    final response = await apiClient.get(
      '/workspaces/$workspaceId/servers/$serverId/services/$serviceName',
    );

    if (response.data is Map<String, dynamic>) {
      return ServiceModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format detail service tidak valid.');
  }

  Future<ServiceActionResultModel> startService(
    String workspaceId,
    String serverId,
    String serviceName,
  ) async {
    return _executeAction(workspaceId, serverId, serviceName, 'start');
  }

  Future<ServiceActionResultModel> stopService(
    String workspaceId,
    String serverId,
    String serviceName,
  ) async {
    return _executeAction(workspaceId, serverId, serviceName, 'stop');
  }

  Future<ServiceActionResultModel> restartService(
    String workspaceId,
    String serverId,
    String serviceName,
  ) async {
    return _executeAction(workspaceId, serverId, serviceName, 'restart');
  }

  Future<ServiceActionResultModel> reloadService(
    String workspaceId,
    String serverId,
    String serviceName,
  ) async {
    return _executeAction(workspaceId, serverId, serviceName, 'reload');
  }

  Future<ServiceActionResultModel> _executeAction(
    String workspaceId,
    String serverId,
    String serviceName,
    String action,
  ) async {
    if (workspaceId.trim().isEmpty || serverId.trim().isEmpty || serviceName.trim().isEmpty) {
      throw ApiException(message: 'Parameter aksi service tidak lengkap.');
    }

    final response = await apiClient.post(
      '/workspaces/$workspaceId/servers/$serverId/services/$serviceName/$action',
      data: {'confirm': true},
    );

    if (response.data is Map<String, dynamic>) {
      return ServiceActionResultModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format hasil aksi service tidak valid.');
  }
}
