import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/server_model.dart';
import '../../../data/models/connection_test_model.dart';
import '../../../data/models/monitoring_metrics_model.dart';
import '../../../data/services/server_service.dart';

import '../../../data/models/agent_model.dart';
import '../../../data/services/agent_service.dart';

class ServerController extends GetxController {
  final ServerService serverService;
  final AgentService? agentService;

  final RxBool isLoading = false.obs;
  final RxBool isCreating = false.obs;
  final RxBool isTestingConnection = false.obs;
  final RxBool isLoadingMetrics = false.obs;
  final RxBool isLoadingAgent = false.obs;
  final RxBool isEnrolling = false.obs;

  final RxList<ServerModel> servers = <ServerModel>[].obs;
  final Rxn<ServerModel> selectedServer = Rxn<ServerModel>();
  final Rxn<ConnectionTestModel> connectionTestResult = Rxn<ConnectionTestModel>();
  final Rxn<ServerMetricsModel> serverMetrics = Rxn<ServerMetricsModel>();
  final Rxn<AgentModel> agent = Rxn<AgentModel>();
  final Rxn<AgentEnrollmentResponseModel> enrollmentData = Rxn<AgentEnrollmentResponseModel>();
  final RxnString errorMessage = RxnString();
  final RxnString metricsErrorMessage = RxnString();

  ServerController({
    required this.serverService,
    this.agentService,
  });

  Future<void> loadServers(String workspaceId, {String? environmentId}) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;

      final list = await serverService.getServers(workspaceId, environmentId: environmentId);
      servers.assignAll(list);
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (_) {
      errorMessage.value = 'Gagal memuat daftar server.';
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> loadServerDetail(String workspaceId, String serverId) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;
      connectionTestResult.value = null;

      final server = await serverService.getServer(workspaceId, serverId);
      selectedServer.value = server;

      // Also attempt to load agent information if connection_type == 'AGENT' or on demand
      await loadAgent(workspaceId, serverId);
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (_) {
      errorMessage.value = 'Gagal memuat detail server.';
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> loadAgent(String workspaceId, String serverId) async {
    try {
      isLoadingAgent.value = true;
      final service = agentService ?? (Get.isRegistered<AgentService>() ? Get.find<AgentService>() : null);
      if (service == null) return;

      final agentData = await service.getAgent(workspaceId, serverId);
      agent.value = agentData;
    } catch (_) {
      agent.value = null;
    } finally {
      isLoadingAgent.value = false;
    }
  }

  Future<AgentEnrollmentResponseModel?> generateEnrollmentToken(
    String workspaceId,
    String serverId, {
    int expiresInMinutes = 15,
  }) async {
    try {
      isEnrolling.value = true;
      final service = agentService ?? (Get.isRegistered<AgentService>() ? Get.find<AgentService>() : null);
      if (service == null) throw ApiException(message: 'AgentService belum terdaftar.');

      final result = await service.createEnrollmentToken(
        workspaceId: workspaceId,
        serverId: serverId,
        expiresInMinutes: expiresInMinutes,
      );
      enrollmentData.value = result;
      Get.snackbar(
        'Enrollment Token Dibuat',
        'Token setup agent siap dijalankan pada target server.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return result;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Generate Token',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
      );
      return null;
    } catch (_) {
      Get.snackbar(
        'Gagal',
        'Terjadi kesalahan saat membuat enrollment token.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return null;
    } finally {
      isEnrolling.value = false;
    }
  }

  Future<bool> disableAgent(String workspaceId, String serverId) async {
    try {
      isLoadingAgent.value = true;
      final service = agentService ?? (Get.isRegistered<AgentService>() ? Get.find<AgentService>() : null);
      if (service == null) throw ApiException(message: 'AgentService belum terdaftar.');

      final updated = await service.disableAgent(workspaceId, serverId);
      agent.value = updated;
      Get.snackbar(
        'Agent Dinonaktifkan',
        'DevOps Agent untuk server ini berhasil dinonaktifkan.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Nonaktifkan Agent',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } finally {
      isLoadingAgent.value = false;
    }
  }

  Future<bool> revokeAgent(String workspaceId, String serverId) async {
    try {
      isLoadingAgent.value = true;
      final service = agentService ?? (Get.isRegistered<AgentService>() ? Get.find<AgentService>() : null);
      if (service == null) throw ApiException(message: 'AgentService belum terdaftar.');

      final updated = await service.revokeAgent(workspaceId, serverId);
      agent.value = updated;
      if (selectedServer.value != null) {
        final s = selectedServer.value!;
        selectedServer.value = ServerModel(
          id: s.id,
          workspaceId: s.workspaceId,
          environmentId: s.environmentId,
          name: s.name,
          hostname: s.hostname,
          ipAddress: s.ipAddress,
          sshPort: s.sshPort,
          username: s.username,
          operatingSystem: s.operatingSystem,
          description: s.description,
          connectionType: 'SSH',
          isActive: s.isActive,
          environment: s.environment,
          hasCredential: s.hasCredential,
          authType: s.authType,
          status: s.status,
          createdAt: s.createdAt,
          updatedAt: s.updatedAt,
        );
      }
      Get.snackbar(
        'Agent Dicabut (Revoked)',
        'Kredensial Agent telah dicabut dan mode dikembalikan ke SSH.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Mencabut Agent',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } finally {
      isLoadingAgent.value = false;
    }
  }

  Future<void> loadServerMetrics(String workspaceId, String serverId, {bool silent = false}) async {
    try {
      if (!silent) {
        isLoadingMetrics.value = true;
      }
      metricsErrorMessage.value = null;

      final metrics = await serverService.getServerMetrics(workspaceId, serverId);
      serverMetrics.value = metrics;

      // Automatically sync online/offline status in server model
      _updateStatusInList(serverId, metrics.status);
    } on ApiException catch (e) {
      metricsErrorMessage.value = e.message;
      if (e.message.toLowerCase().contains('timeout') || e.message.toLowerCase().contains('gagal terhubung')) {
        _updateStatusInList(serverId, 'OFFLINE');
      }
    } catch (_) {
      metricsErrorMessage.value = 'Gagal memuat metrik server.';
    } finally {
      isLoadingMetrics.value = false;
    }
  }

  Future<bool> createServer({
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
    try {
      isCreating.value = true;
      errorMessage.value = null;

      final newServer = await serverService.createServer(
        workspaceId: workspaceId,
        environmentId: environmentId,
        name: name,
        hostname: hostname,
        ipAddress: ipAddress,
        sshPort: sshPort,
        username: username,
        operatingSystem: operatingSystem,
        description: description,
        isActive: isActive,
        authType: authType,
        password: password,
        privateKey: privateKey,
        passphrase: passphrase,
      );

      servers.add(newServer);
      Get.snackbar(
        'Server Ditambahkan',
        'Server "${newServer.name}" berhasil ditambahkan.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Menambahkan Server',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } catch (_) {
      Get.snackbar(
        'Gagal',
        'Terjadi kesalahan saat menambahkan server.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } finally {
      isCreating.value = false;
    }
  }

  Future<bool> deleteServer(String workspaceId, String serverId) async {
    try {
      isLoading.value = true;
      await serverService.deleteServer(workspaceId, serverId);
      servers.removeWhere((s) => s.id == serverId);
      Get.snackbar(
        'Berhasil',
        'Server berhasil dihapus.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Menghapus',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> testConnection(String workspaceId, String serverId) async {
    try {
      isTestingConnection.value = true;
      connectionTestResult.value = null;

      final res = await serverService.testConnection(workspaceId, serverId);
      connectionTestResult.value = res;

      final updatedStatus = res.status;

      // Update selected server status in-memory
      if (selectedServer.value != null && selectedServer.value!.id == serverId) {
        selectedServer.value = ServerModel(
          id: selectedServer.value!.id,
          workspaceId: selectedServer.value!.workspaceId,
          environmentId: selectedServer.value!.environmentId,
          name: selectedServer.value!.name,
          hostname: selectedServer.value!.hostname,
          ipAddress: selectedServer.value!.ipAddress,
          sshPort: selectedServer.value!.sshPort,
          username: selectedServer.value!.username,
          operatingSystem: selectedServer.value!.operatingSystem,
          description: selectedServer.value!.description,
          isActive: selectedServer.value!.isActive,
          environment: selectedServer.value!.environment,
          hasCredential: selectedServer.value!.hasCredential,
          authType: selectedServer.value!.authType,
          status: updatedStatus,
          createdAt: selectedServer.value!.createdAt,
          updatedAt: selectedServer.value!.updatedAt,
        );
      }

      // Update in servers list for WorkspaceHomeView
      final idx = servers.indexWhere((s) => s.id == serverId);
      if (idx != -1) {
        final existing = servers[idx];
        servers[idx] = ServerModel(
          id: existing.id,
          workspaceId: existing.workspaceId,
          environmentId: existing.environmentId,
          name: existing.name,
          hostname: existing.hostname,
          ipAddress: existing.ipAddress,
          sshPort: existing.sshPort,
          username: existing.username,
          operatingSystem: existing.operatingSystem,
          description: existing.description,
          isActive: existing.isActive,
          environment: existing.environment,
          hasCredential: existing.hasCredential,
          authType: existing.authType,
          status: updatedStatus,
          createdAt: existing.createdAt,
          updatedAt: existing.updatedAt,
        );
      }
    } on ApiException catch (e) {
      connectionTestResult.value = ConnectionTestModel(
        success: false,
        message: e.message,
        status: 'OFFLINE',
      );
      _updateStatusInList(serverId, 'OFFLINE');
    } catch (e) {
      connectionTestResult.value = ConnectionTestModel(
        success: false,
        message: 'Gagal menguji koneksi SSH.',
        status: 'OFFLINE',
      );
      _updateStatusInList(serverId, 'OFFLINE');
    } finally {
      isTestingConnection.value = false;
    }
  }

  void _updateStatusInList(String serverId, String status) {
    if (selectedServer.value != null && selectedServer.value!.id == serverId) {
      final s = selectedServer.value!;
      selectedServer.value = ServerModel(
        id: s.id,
        workspaceId: s.workspaceId,
        environmentId: s.environmentId,
        name: s.name,
        hostname: s.hostname,
        ipAddress: s.ipAddress,
        sshPort: s.sshPort,
        username: s.username,
        operatingSystem: s.operatingSystem,
        description: s.description,
        isActive: s.isActive,
        environment: s.environment,
        hasCredential: s.hasCredential,
        authType: s.authType,
        status: status,
        createdAt: s.createdAt,
        updatedAt: s.updatedAt,
      );
    }

    final idx = servers.indexWhere((s) => s.id == serverId);
    if (idx != -1) {
      final existing = servers[idx];
      servers[idx] = ServerModel(
        id: existing.id,
        workspaceId: existing.workspaceId,
        environmentId: existing.environmentId,
        name: existing.name,
        hostname: existing.hostname,
        ipAddress: existing.ipAddress,
        sshPort: existing.sshPort,
        username: existing.username,
        operatingSystem: existing.operatingSystem,
        description: existing.description,
        isActive: existing.isActive,
        environment: existing.environment,
        hasCredential: existing.hasCredential,
        authType: existing.authType,
        status: status,
        createdAt: existing.createdAt,
        updatedAt: existing.updatedAt,
      );
    }
  }
}
