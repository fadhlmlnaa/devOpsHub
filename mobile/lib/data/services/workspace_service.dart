import '../models/workspace_model.dart';
import '../../core/network/api_client.dart';

class WorkspaceService {
  final ApiClient apiClient;

  WorkspaceService({required this.apiClient});

  Future<List<WorkspaceModel>> getWorkspaces() async {
    final response = await apiClient.get('/workspaces');
    final data = response.data;
    if (data is List) {
      return data
          .map((item) => WorkspaceModel.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  Future<WorkspaceModel> getWorkspace(String id) async {
    final response = await apiClient.get('/workspaces/$id');
    return WorkspaceModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<WorkspaceModel> createWorkspace({
    required String name,
    String? description,
    String timezone = 'Asia/Jakarta',
  }) async {
    final response = await apiClient.post(
      '/workspaces',
      data: {
        'name': name.trim(),
        'description': description?.trim().isEmpty == true ? null : description?.trim(),
        'timezone': timezone,
      },
    );
    return WorkspaceModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<WorkspaceModel> updateWorkspace({
    required String id,
    String? name,
    String? description,
    String? timezone,
  }) async {
    final payload = <String, dynamic>{};
    if (name != null) payload['name'] = name.trim();
    if (description != null) payload['description'] = description.trim();
    if (timezone != null) payload['timezone'] = timezone;

    final response = await apiClient.patch(
      '/workspaces/$id',
      data: payload,
    );
    return WorkspaceModel.fromJson(response.data as Map<String, dynamic>);
  }
}
