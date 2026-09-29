import 'package:dio/dio.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../models/backup_model.dart';

class BackupService {
  final ApiClient apiClient;

  BackupService({required this.apiClient});

  // --- Backup Configs ---

  Future<List<BackupConfigModel>> getBackupConfigs(
    String workspaceId, {
    String? environmentId,
    String? serverId,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/backup-configs',
        queryParameters: {
          if (environmentId != null && environmentId.isNotEmpty) 'environment_id': environmentId,
          if (serverId != null && serverId.isNotEmpty) 'server_id': serverId,
        },
      );
      final List<dynamic> data = response.data as List<dynamic>;
      return data.map((item) => BackupConfigModel.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<BackupConfigModel> getBackupConfigDetail(
    String workspaceId,
    String configId,
  ) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/backup-configs/$configId',
      );
      return BackupConfigModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<BackupConfigModel> createBackupConfig(
    String workspaceId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await apiClient.dio.post(
        '/workspaces/$workspaceId/backup-configs',
        data: data,
      );
      return BackupConfigModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<BackupConfigModel> updateBackupConfig(
    String workspaceId,
    String configId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await apiClient.dio.patch(
        '/workspaces/$workspaceId/backup-configs/$configId',
        data: data,
      );
      return BackupConfigModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<void> deleteBackupConfig(
    String workspaceId,
    String configId,
  ) async {
    try {
      await apiClient.dio.delete(
        '/workspaces/$workspaceId/backup-configs/$configId',
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // --- Backup Execution & Verification ---

  Future<BackupModel> triggerBackup(
    String workspaceId,
    String configId, {
    required bool confirm,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/workspaces/$workspaceId/backup-configs/$configId/run',
        data: {'confirm': confirm},
      );
      return BackupModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<BackupVerifyResultModel> verifyBackup(
    String workspaceId,
    String backupId, {
    bool confirm = true,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/workspaces/$workspaceId/backups/$backupId/verify',
        data: {'confirm': confirm},
      );
      return BackupVerifyResultModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // --- Backup History & Logs ---

  Future<List<BackupModel>> getBackups(
    String workspaceId, {
    String? environmentId,
    String? serverId,
    String? backupConfigId,
    String? backupType,
    String? status,
    int page = 1,
    int limit = 20,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/backups',
        queryParameters: {
          if (environmentId != null && environmentId.isNotEmpty) 'environment_id': environmentId,
          if (serverId != null && serverId.isNotEmpty) 'server_id': serverId,
          if (backupConfigId != null && backupConfigId.isNotEmpty) 'backup_config_id': backupConfigId,
          if (backupType != null && backupType.isNotEmpty) 'backup_type': backupType,
          if (status != null && status.isNotEmpty) 'status': status,
          'page': page,
          'limit': limit,
        },
      );
      final Map<String, dynamic> data = response.data as Map<String, dynamic>;
      final List<dynamic> items = data['items'] as List<dynamic>? ?? [];
      return items.map((item) => BackupModel.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<BackupModel> getBackupDetail(
    String workspaceId,
    String backupId,
  ) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/backups/$backupId',
      );
      return BackupModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<BackupLogsModel> getBackupLogs(
    String workspaceId,
    String backupId, {
    int lines = 100,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/backups/$backupId/logs',
        queryParameters: {'lines': lines},
      );
      return BackupLogsModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
