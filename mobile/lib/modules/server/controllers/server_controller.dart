import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/server_model.dart';
import '../../../data/models/connection_test_model.dart';
import '../../../data/services/server_service.dart';

class ServerController extends GetxController {
  final ServerService serverService;

  final RxBool isLoading = false.obs;
  final RxBool isCreating = false.obs;
  final RxBool isTestingConnection = false.obs;
  final RxList<ServerModel> servers = <ServerModel>[].obs;
  final Rxn<ServerModel> selectedServer = Rxn<ServerModel>();
  final Rxn<ConnectionTestModel> connectionTestResult = Rxn<ConnectionTestModel>();
  final RxnString errorMessage = RxnString();

  ServerController({required this.serverService});

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
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (_) {
      errorMessage.value = 'Gagal memuat detail server.';
    } finally {
      isLoading.value = false;
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
          status: res.status,
          createdAt: selectedServer.value!.createdAt,
          updatedAt: selectedServer.value!.updatedAt,
        );
      }
    } on ApiException catch (e) {
      connectionTestResult.value = ConnectionTestModel(
        success: false,
        message: e.message,
        status: 'OFFLINE',
      );
    } catch (e) {
      connectionTestResult.value = ConnectionTestModel(
        success: false,
        message: 'Gagal menguji koneksi SSH.',
        status: 'OFFLINE',
      );
    } finally {
      isTestingConnection.value = false;
    }
  }
}
