import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../models/docker_model.dart';

class DockerService {
  final ApiClient apiClient;

  DockerService({required this.apiClient});

  String _base(String workspaceId, String serverId) =>
      '/workspaces/$workspaceId/servers/$serverId/docker';

  // 1. Docker Status
  Future<DockerStatusModel> getDockerStatus(String workspaceId, String serverId) async {
    if (workspaceId.trim().isEmpty || serverId.trim().isEmpty) {
      throw ApiException(message: 'ID Workspace atau Server tidak valid.');
    }

    final response = await apiClient.get(_base(workspaceId, serverId));
    if (response.data is Map<String, dynamic>) {
      return DockerStatusModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format status Docker tidak valid.');
  }

  // 2. Containers List
  Future<List<DockerContainerModel>> getContainers(
    String workspaceId,
    String serverId, {
    String state = 'running',
  }) async {
    if (workspaceId.trim().isEmpty || serverId.trim().isEmpty) {
      throw ApiException(message: 'ID Workspace atau Server tidak valid.');
    }

    final response = await apiClient.get(
      '${_base(workspaceId, serverId)}/containers',
      queryParameters: {'state': state},
    );

    if (response.data is Map<String, dynamic>) {
      final map = response.data as Map<String, dynamic>;
      final list = (map['containers'] as List<dynamic>?)
              ?.map((c) => DockerContainerModel.fromJson(c as Map<String, dynamic>))
              .toList() ??
          [];
      return list;
    }
    throw ApiException(message: 'Format daftar container tidak valid.');
  }

  // 3. Container Detail
  Future<DockerContainerDetailModel> getContainerDetail(
    String workspaceId,
    String serverId,
    String containerId,
  ) async {
    if (workspaceId.trim().isEmpty || serverId.trim().isEmpty || containerId.trim().isEmpty) {
      throw ApiException(message: 'Parameter container tidak lengkap.');
    }

    final response = await apiClient.get(
      '${_base(workspaceId, serverId)}/containers/$containerId',
    );

    if (response.data is Map<String, dynamic>) {
      return DockerContainerDetailModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format detail container tidak valid.');
  }

  // 4. Container Mutations (Start / Stop / Restart)
  Future<DockerContainerActionResultModel> startContainer(
    String workspaceId,
    String serverId,
    String containerId,
  ) async {
    final response = await apiClient.post(
      '${_base(workspaceId, serverId)}/containers/$containerId/start',
      data: {'confirm': true},
    );
    if (response.data is Map<String, dynamic>) {
      return DockerContainerActionResultModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format respon aksi container tidak valid.');
  }

  Future<DockerContainerActionResultModel> stopContainer(
    String workspaceId,
    String serverId,
    String containerId,
  ) async {
    final response = await apiClient.post(
      '${_base(workspaceId, serverId)}/containers/$containerId/stop',
      data: {'confirm': true},
    );
    if (response.data is Map<String, dynamic>) {
      return DockerContainerActionResultModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format respon aksi container tidak valid.');
  }

  Future<DockerContainerActionResultModel> restartContainer(
    String workspaceId,
    String serverId,
    String containerId,
  ) async {
    final response = await apiClient.post(
      '${_base(workspaceId, serverId)}/containers/$containerId/restart',
      data: {'confirm': true},
    );
    if (response.data is Map<String, dynamic>) {
      return DockerContainerActionResultModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format respon aksi container tidak valid.');
  }

  // 5. Container Logs
  Future<DockerContainerLogsModel> getContainerLogs(
    String workspaceId,
    String serverId,
    String containerId, {
    int lines = 100,
    String? since,
  }) async {
    final queryParams = <String, dynamic>{'lines': lines};
    if (since != null && since.isNotEmpty) {
      queryParams['since'] = since;
    }

    final response = await apiClient.get(
      '${_base(workspaceId, serverId)}/containers/$containerId/logs',
      queryParameters: queryParams,
    );

    if (response.data is Map<String, dynamic>) {
      return DockerContainerLogsModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format respon log container tidak valid.');
  }

  // 6. Docker Compose Projects CRUD
  Future<List<DockerComposeProjectModel>> getComposeProjects(
    String workspaceId,
    String serverId,
  ) async {
    final response = await apiClient.get('${_base(workspaceId, serverId)}/compose/projects');
    if (response.data is List) {
      return (response.data as List)
          .map((p) => DockerComposeProjectModel.fromJson(p as Map<String, dynamic>))
          .toList();
    }
    throw ApiException(message: 'Format daftar compose project tidak valid.');
  }

  Future<DockerComposeProjectModel> createComposeProject(
    String workspaceId,
    String serverId,
    Map<String, dynamic> data,
  ) async {
    final response = await apiClient.post(
      '${_base(workspaceId, serverId)}/compose/projects',
      data: data,
    );
    if (response.data is Map<String, dynamic>) {
      return DockerComposeProjectModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format registrasi compose project tidak valid.');
  }

  Future<DockerComposeProjectModel> getComposeProject(
    String workspaceId,
    String serverId,
    String projectId,
  ) async {
    final response = await apiClient.get(
      '${_base(workspaceId, serverId)}/compose/projects/$projectId',
    );
    if (response.data is Map<String, dynamic>) {
      return DockerComposeProjectModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format detail compose project tidak valid.');
  }

  Future<DockerComposeProjectModel> updateComposeProject(
    String workspaceId,
    String serverId,
    String projectId,
    Map<String, dynamic> data,
  ) async {
    final response = await apiClient.patch(
      '${_base(workspaceId, serverId)}/compose/projects/$projectId',
      data: data,
    );
    if (response.data is Map<String, dynamic>) {
      return DockerComposeProjectModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format update compose project tidak valid.');
  }

  Future<void> deleteComposeProject(
    String workspaceId,
    String serverId,
    String projectId,
  ) async {
    await apiClient.delete('${_base(workspaceId, serverId)}/compose/projects/$projectId');
  }

  // 7. Compose Operations (Status, Up, Down, Restart)
  Future<DockerComposeStatusModel> getComposeStatus(
    String workspaceId,
    String serverId,
    String projectId,
  ) async {
    final response = await apiClient.get(
      '${_base(workspaceId, serverId)}/compose/projects/$projectId/status',
    );
    if (response.data is Map<String, dynamic>) {
      return DockerComposeStatusModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format status compose tidak valid.');
  }

  Future<DockerComposeActionResultModel> composeUp(
    String workspaceId,
    String serverId,
    String projectId,
  ) async {
    final response = await apiClient.post(
      '${_base(workspaceId, serverId)}/compose/projects/$projectId/up',
      data: {'confirm': true},
    );
    if (response.data is Map<String, dynamic>) {
      return DockerComposeActionResultModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format respon compose up tidak valid.');
  }

  Future<DockerComposeActionResultModel> composeDown(
    String workspaceId,
    String serverId,
    String projectId,
  ) async {
    final response = await apiClient.post(
      '${_base(workspaceId, serverId)}/compose/projects/$projectId/down',
      data: {'confirm': true},
    );
    if (response.data is Map<String, dynamic>) {
      return DockerComposeActionResultModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format respon compose down tidak valid.');
  }

  Future<DockerComposeActionResultModel> composeRestart(
    String workspaceId,
    String serverId,
    String projectId,
  ) async {
    final response = await apiClient.post(
      '${_base(workspaceId, serverId)}/compose/projects/$projectId/restart',
      data: {'confirm': true},
    );
    if (response.data is Map<String, dynamic>) {
      return DockerComposeActionResultModel.fromJson(response.data as Map<String, dynamic>);
    }
    throw ApiException(message: 'Format respon compose restart tidak valid.');
  }
}
