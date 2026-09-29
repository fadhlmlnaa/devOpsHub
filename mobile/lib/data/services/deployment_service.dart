import 'package:dio/dio.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../models/deployment_model.dart';

class DeploymentService {
  final ApiClient apiClient;

  DeploymentService({required this.apiClient});

  // --- Deployment Configs ---

  Future<List<DeploymentConfigModel>> getDeploymentConfigs(
    String workspaceId, {
    String? environmentId,
    String? serverId,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/deployment-configs',
        queryParameters: {
          if (environmentId != null && environmentId.isNotEmpty)
            'environment_id': environmentId,
          if (serverId != null && serverId.isNotEmpty) 'server_id': serverId,
        },
      );
      final List<dynamic> data = response.data as List<dynamic>;
      return data
          .map((item) =>
              DeploymentConfigModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<DeploymentConfigModel> getDeploymentConfig(
    String workspaceId,
    String configId,
  ) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/deployment-configs/$configId',
      );
      return DeploymentConfigModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<DeploymentConfigModel> createDeploymentConfig(
    String workspaceId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await apiClient.dio.post(
        '/workspaces/$workspaceId/deployment-configs',
        data: data,
      );
      return DeploymentConfigModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<DeploymentConfigModel> updateDeploymentConfig(
    String workspaceId,
    String configId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await apiClient.dio.patch(
        '/workspaces/$workspaceId/deployment-configs/$configId',
        data: data,
      );
      return DeploymentConfigModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<void> deleteDeploymentConfig(
    String workspaceId,
    String configId,
  ) async {
    try {
      await apiClient.dio.delete(
        '/workspaces/$workspaceId/deployment-configs/$configId',
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // --- Trigger Deployment ---

  Future<DeploymentModel> triggerDeployment(
    String workspaceId,
    String configId, {
    bool confirm = true,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/workspaces/$workspaceId/deployment-configs/$configId/deploy',
        data: {'confirm': confirm},
      );
      return DeploymentModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // --- Deployment History & Logs ---

  Future<List<DeploymentModel>> getDeployments(
    String workspaceId, {
    String? environmentId,
    String? serverId,
    String? deploymentConfigId,
    String? status,
    int page = 1,
    int limit = 20,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/deployments',
        queryParameters: {
          if (environmentId != null && environmentId.isNotEmpty)
            'environment_id': environmentId,
          if (serverId != null && serverId.isNotEmpty) 'server_id': serverId,
          if (deploymentConfigId != null && deploymentConfigId.isNotEmpty)
            'deployment_config_id': deploymentConfigId,
          if (status != null && status.isNotEmpty) 'status': status,
          'page': page,
          'limit': limit,
        },
      );
      final Map<String, dynamic> body = response.data as Map<String, dynamic>;
      final List<dynamic> items = body['items'] as List<dynamic>? ?? [];
      return items
          .map((item) => DeploymentModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<DeploymentModel> getDeployment(
    String workspaceId,
    String deploymentId,
  ) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/deployments/$deploymentId',
      );
      return DeploymentModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<DeploymentLogsModel> getDeploymentLogs(
    String workspaceId,
    String deploymentId, {
    int lines = 100,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/deployments/$deploymentId/logs',
        queryParameters: {'lines': lines},
      );
      return DeploymentLogsModel.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
