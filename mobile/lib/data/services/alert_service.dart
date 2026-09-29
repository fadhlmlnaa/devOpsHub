import 'package:dio/dio.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../models/alert_model.dart';

class AlertService {
  final ApiClient apiClient;

  AlertService({required this.apiClient});

  // --- Alert Rules ---

  Future<List<AlertRuleModel>> getAlertRules(
    String workspaceId, {
    String? environmentId,
    String? serverId,
    bool? isEnabled,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/alert-rules',
        queryParameters: {
          if (environmentId != null && environmentId.isNotEmpty) 'environment_id': environmentId,
          if (serverId != null && serverId.isNotEmpty) 'server_id': serverId,
          'is_enabled': ?isEnabled,
        },
      );
      final List<dynamic> data = response.data as List<dynamic>;
      return data.map((item) => AlertRuleModel.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<AlertRuleModel> getAlertRule(String workspaceId, String ruleId) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/alert-rules/$ruleId',
      );
      return AlertRuleModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<AlertRuleModel> createAlertRule(
    String workspaceId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await apiClient.dio.post(
        '/workspaces/$workspaceId/alert-rules',
        data: data,
      );
      return AlertRuleModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<AlertRuleModel> updateAlertRule(
    String workspaceId,
    String ruleId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await apiClient.dio.patch(
        '/workspaces/$workspaceId/alert-rules/$ruleId',
        data: data,
      );
      return AlertRuleModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<void> deleteAlertRule(String workspaceId, String ruleId) async {
    try {
      await apiClient.dio.delete(
        '/workspaces/$workspaceId/alert-rules/$ruleId',
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // --- Alerts ---

  Future<List<AlertModel>> getAlerts(
    String workspaceId, {
    String? status,
    String? severity,
    String? serverId,
    String? environmentId,
    String? alertRuleId,
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/alerts',
        queryParameters: {
          if (status != null && status.isNotEmpty && status != 'ALL') 'status': status,
          if (severity != null && severity.isNotEmpty && severity != 'ALL') 'severity': severity,
          if (serverId != null && serverId.isNotEmpty) 'server_id': serverId,
          if (environmentId != null && environmentId.isNotEmpty) 'environment_id': environmentId,
          if (alertRuleId != null && alertRuleId.isNotEmpty) 'alert_rule_id': alertRuleId,
          'limit': limit,
          'offset': offset,
        },
      );
      final List<dynamic> data = response.data as List<dynamic>;
      return data.map((item) => AlertModel.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<AlertModel> getAlertDetail(String workspaceId, String alertId) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/alerts/$alertId',
      );
      return AlertModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<List<AlertEventModel>> getAlertEvents(String workspaceId, String alertId) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/alerts/$alertId/events',
      );
      final List<dynamic> data = response.data as List<dynamic>;
      return data.map((item) => AlertEventModel.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<AlertModel> resolveAlert(
    String workspaceId,
    String alertId, {
    bool confirm = true,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/workspaces/$workspaceId/alerts/$alertId/resolve',
        data: {'confirm': confirm},
      );
      return AlertModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<Map<String, dynamic>> evaluateAlerts(String workspaceId) async {
    try {
      final response = await apiClient.dio.post(
        '/workspaces/$workspaceId/alerts/evaluate',
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // --- Notifications ---

  Future<List<NotificationModel>> getNotifications(
    String workspaceId, {
    bool? unreadOnly,
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/notifications',
        queryParameters: {
          'unread_only': ?unreadOnly,
          'limit': limit,
          'offset': offset,
        },
      );
      final List<dynamic> data = response.data as List<dynamic>;
      return data.map((item) => NotificationModel.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<NotificationModel> markNotificationRead(
    String workspaceId,
    String notificationId,
  ) async {
    try {
      final response = await apiClient.dio.patch(
        '/workspaces/$workspaceId/notifications/$notificationId/read',
      );
      return NotificationModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<void> markAllNotificationsRead(String workspaceId) async {
    try {
      await apiClient.dio.post(
        '/workspaces/$workspaceId/notifications/mark-all-read',
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<UnreadNotificationCountModel> getUnreadNotificationCount(String workspaceId) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/notifications/unread-count',
      );
      return UnreadNotificationCountModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<NotificationPreferenceModel> getNotificationPreferences(String workspaceId) async {
    try {
      final response = await apiClient.dio.get(
        '/workspaces/$workspaceId/notification-preferences',
      );
      return NotificationPreferenceModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<NotificationPreferenceModel> updateNotificationPreferences(
    String workspaceId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await apiClient.dio.patch(
        '/workspaces/$workspaceId/notification-preferences',
        data: data,
      );
      return NotificationPreferenceModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
