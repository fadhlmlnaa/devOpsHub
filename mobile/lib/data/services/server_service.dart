import '../models/server_model.dart';
import '../models/connection_test_model.dart';
import '../../core/network/api_client.dart';

class ServerService {
  final ApiClient apiClient;

  ServerService({required this.apiClient});

  Future<List<ServerModel>> getServers(String workspaceId, {String? environmentId}) async {
    final params = <String, dynamic>{};
    if (environmentId != null && environmentId.isNotEmpty) {
      params['environment_id'] = environmentId;
    }

    final response = await apiClient.get(
      '/workspaces/$workspaceId/servers',
      queryParameters: params.isNotEmpty ? params : null,
    );
    final data = response.data;
    if (data is List) {
      return data.map((item) => ServerModel.fromJson(item as Map<String, dynamic>)).toList();
    }
    return [];
  }

  Future<ServerModel> getServer(String workspaceId, String serverId) async {
    final response = await apiClient.get('/workspaces/$workspaceId/servers/$serverId');
    return ServerModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ServerModel> createServer({
    required String workspaceId,
    required String environmentId,
    required String name,
    String? hostname,
    String? ipAddress,
    int sshPort = 22,
    String? username,
    String? operatingSystem,
    String? description,
    bool isActive = true,
    String? authType,
    String? password,
    String? privateKey,
    String? passphrase,
  }) async {
    final payload = <String, dynamic>{
      'environment_id': environmentId,
      'name': name.trim(),
      if (hostname != null && hostname.trim().isNotEmpty) 'hostname': hostname.trim(),
      if (ipAddress != null && ipAddress.trim().isNotEmpty) 'ip_address': ipAddress.trim(),
      'ssh_port': sshPort,
      if (username != null && username.trim().isNotEmpty) 'username': username.trim(),
      if (operatingSystem != null && operatingSystem.trim().isNotEmpty) 'operating_system': operatingSystem.trim(),
      if (description != null && description.trim().isNotEmpty) 'description': description.trim(),
      'is_active': isActive,
    };

    if (authType != null && authType.isNotEmpty) {
      payload['credential'] = {
        'auth_type': authType,
        'username': (username != null && username.trim().isNotEmpty) ? username.trim() : 'root',
        if (password != null && password.isNotEmpty) 'password': password,
        if (privateKey != null && privateKey.isNotEmpty) 'private_key': privateKey,
        if (passphrase != null && passphrase.isNotEmpty) 'passphrase': passphrase,
      };
    }

    final response = await apiClient.post(
      '/workspaces/$workspaceId/servers',
      data: payload,
    );
    return ServerModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ServerModel> updateServer({
    required String workspaceId,
    required String serverId,
    String? environmentId,
    String? name,
    String? hostname,
    String? ipAddress,
    int? sshPort,
    String? username,
    String? operatingSystem,
    String? description,
    bool? isActive,
    String? authType,
    String? password,
    String? privateKey,
    String? passphrase,
  }) async {
    final payload = <String, dynamic>{};
    if (environmentId != null) payload['environment_id'] = environmentId;
    if (name != null) payload['name'] = name.trim();
    if (hostname != null) payload['hostname'] = hostname.trim();
    if (ipAddress != null) payload['ip_address'] = ipAddress.trim();
    if (sshPort != null) payload['ssh_port'] = sshPort;
    if (username != null) payload['username'] = username.trim();
    if (operatingSystem != null) payload['operating_system'] = operatingSystem.trim();
    if (description != null) payload['description'] = description.trim();
    if (isActive != null) payload['is_active'] = isActive;

    if (authType != null) {
      final cred = <String, dynamic>{
        'auth_type': authType,
        'username': username ?? 'root',
      };
      if (password != null) cred['password'] = password;
      if (privateKey != null) cred['private_key'] = privateKey;
      if (passphrase != null) cred['passphrase'] = passphrase;
      payload['credential'] = cred;
    }

    final response = await apiClient.patch(
      '/workspaces/$workspaceId/servers/$serverId',
      data: payload,
    );
    return ServerModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteServer(String workspaceId, String serverId) async {
    await apiClient.delete('/workspaces/$workspaceId/servers/$serverId');
  }

  Future<ConnectionTestModel> testConnection(String workspaceId, String serverId) async {
    final response = await apiClient.post(
      '/workspaces/$workspaceId/servers/$serverId/connection-test',
    );
    return ConnectionTestModel.fromJson(response.data as Map<String, dynamic>);
  }
}
