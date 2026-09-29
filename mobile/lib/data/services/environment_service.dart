import '../models/environment_model.dart';
import '../../core/network/api_client.dart';

class EnvironmentService {
  final ApiClient apiClient;

  EnvironmentService({required this.apiClient});

  Future<List<EnvironmentModel>> getEnvironments(String workspaceId) async {
    final response = await apiClient.get('/workspaces/$workspaceId/environments');
    final data = response.data;
    if (data is List) {
      return data
          .map((item) => EnvironmentModel.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  Future<EnvironmentModel> getEnvironment(String workspaceId, String environmentId) async {
    final response = await apiClient.get('/workspaces/$workspaceId/environments/$environmentId');
    return EnvironmentModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<EnvironmentModel> createEnvironment({
    required String workspaceId,
    required String name,
    required String key,
    String? description,
  }) async {
    final response = await apiClient.post(
      '/workspaces/$workspaceId/environments',
      data: {
        'name': name.trim(),
        'key': key.trim().toLowerCase(),
        'description': description?.trim().isEmpty == true ? null : description?.trim(),
      },
    );
    return EnvironmentModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<EnvironmentModel> updateEnvironment({
    required String workspaceId,
    required String environmentId,
    String? name,
    String? description,
  }) async {
    final payload = <String, dynamic>{};
    if (name != null) payload['name'] = name.trim();
    if (description != null) payload['description'] = description.trim();

    final response = await apiClient.patch(
      '/workspaces/$workspaceId/environments/$environmentId',
      data: payload,
    );
    return EnvironmentModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteEnvironment(String workspaceId, String environmentId) async {
    await apiClient.delete('/workspaces/$workspaceId/environments/$environmentId');
  }
}
