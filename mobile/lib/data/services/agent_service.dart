import '../models/agent_model.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';

class AgentService {
  final ApiClient apiClient;

  AgentService({required this.apiClient});

  Future<AgentModel?> getAgent(String workspaceId, String serverId) async {
    try {
      final response = await apiClient.get('/workspaces/$workspaceId/servers/$serverId/agent');
      if (response.data is Map<String, dynamic>) {
        return AgentModel.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } on ApiException catch (e) {
      if (e.statusCode == 404) {
        return null;
      }
      rethrow;
    } catch (_) {
      return null;
    }
  }

  Future<AgentEnrollmentResponseModel> createEnrollmentToken({
    required String workspaceId,
    required String serverId,
    int expiresInMinutes = 15,
  }) async {
    final response = await apiClient.post(
      '/workspaces/$workspaceId/servers/$serverId/agent/enrollment',
      data: {'expires_in_minutes': expiresInMinutes},
    );
    if (response.data is Map<String, dynamic>) {
      return AgentEnrollmentResponseModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Gagal membuat enrollment token agent.');
  }

  Future<AgentModel> disableAgent(String workspaceId, String serverId) async {
    final response = await apiClient.post('/workspaces/$workspaceId/servers/$serverId/agent/disable');
    if (response.data is Map<String, dynamic>) {
      return AgentModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Gagal menonaktifkan agent.');
  }

  Future<AgentModel> revokeAgent(String workspaceId, String serverId) async {
    final response = await apiClient.post('/workspaces/$workspaceId/servers/$serverId/agent/revoke');
    if (response.data is Map<String, dynamic>) {
      return AgentModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Gagal mencabut kredensial agent.');
  }

  Future<List<AgentJobModel>> getAgentJobs(String workspaceId, String serverId, {int limit = 20}) async {
    final response = await apiClient.get(
      '/workspaces/$workspaceId/servers/$serverId/agent/jobs',
      queryParameters: {'limit': limit},
    );
    final data = response.data;
    if (data is List) {
      return data.map((item) => AgentJobModel.fromJson(item as Map<String, dynamic>)).toList();
    }
    return [];
  }
}
