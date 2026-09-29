import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/docker_model.dart';
import '../../../data/services/docker_service.dart';

class DockerComposeController extends GetxController {
  final DockerService dockerService;

  DockerComposeController({required this.dockerService});

  final RxBool isLoading = false.obs;
  final RxBool isActionLoading = false.obs;
  final RxString errorMessage = ''.obs;

  final RxList<DockerComposeProjectModel> projects = <DockerComposeProjectModel>[].obs;
  final RxMap<String, DockerComposeStatusModel> projectStatuses = <String, DockerComposeStatusModel>{}.obs;

  final RxString currentWorkspaceId = ''.obs;
  final RxString currentServerId = ''.obs;
  final RxString currentUserRole = 'VIEWER'.obs;

  bool get canMutate =>
      currentUserRole.value.toUpperCase() == 'OWNER' ||
      currentUserRole.value.toUpperCase() == 'ADMIN';

  void initContext({
    required String workspaceId,
    required String serverId,
    String userRole = 'VIEWER',
  }) {
    currentWorkspaceId.value = workspaceId;
    currentServerId.value = serverId;
    currentUserRole.value = userRole;
    loadComposeProjects();
  }

  Future<void> loadComposeProjects({bool silent = false}) async {
    if (currentWorkspaceId.value.isEmpty || currentServerId.value.isEmpty) return;

    if (!silent) {
      isLoading.value = true;
      errorMessage.value = '';
    }

    try {
      final res = await dockerService.getComposeProjects(
        currentWorkspaceId.value,
        currentServerId.value,
      );
      projects.assignAll(res);
      // Load statuses asynchronously for each project
      for (final p in res) {
        loadProjectStatus(p.id, silent: true);
      }
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Gagal memuat Docker Compose projects.';
    } finally {
      if (!silent) isLoading.value = false;
    }
  }

  Future<void> loadProjectStatus(String projectId, {bool silent = false}) async {
    try {
      final statusRes = await dockerService.getComposeStatus(
        currentWorkspaceId.value,
        currentServerId.value,
        projectId,
      );
      projectStatuses[projectId] = statusRes;
    } catch (e) {
      // Ignored on bulk load
    }
  }

  Future<bool> createProject({
    required String name,
    required String projectName,
    required String environmentId,
    required String workingDirectory,
    String composeFile = 'docker-compose.yml',
    String? description,
  }) async {
    if (!canMutate) {
      Get.snackbar('Akses Ditolak', 'Hanya Admin/Owner yang dapat mendaftarkan Compose project.');
      return false;
    }

    isLoading.value = true;
    try {
      final data = {
        'name': name.trim(),
        'project_name': projectName.trim().toLowerCase(),
        'environment_id': environmentId,
        'working_directory': workingDirectory.trim(),
        'compose_file': composeFile.trim(),
        'description': description?.trim(),
        'is_active': true,
      };

      await dockerService.createComposeProject(
        currentWorkspaceId.value,
        currentServerId.value,
        data,
      );

      Get.snackbar('Berhasil', 'Docker Compose project berhasil didaftarkan.', backgroundColor: Colors.teal, colorText: Colors.white);
      loadComposeProjects();
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Registrasi', e.message, backgroundColor: Colors.red, colorText: Colors.white);
      return false;
    } catch (e) {
      Get.snackbar('Gagal Registrasi', '$e', backgroundColor: Colors.red, colorText: Colors.white);
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> deleteProject(String projectId) async {
    if (!canMutate) return;
    try {
      await dockerService.deleteComposeProject(
        currentWorkspaceId.value,
        currentServerId.value,
        projectId,
      );
      Get.snackbar('Berhasil', 'Docker Compose project berhasil dihapus.');
      loadComposeProjects();
    } on ApiException catch (e) {
      Get.snackbar('Gagal Menghapus', e.message, backgroundColor: Colors.red, colorText: Colors.white);
    }
  }

  Future<void> executeComposeAction(String projectId, String action) async {
    if (!canMutate) return;

    isActionLoading.value = true;
    try {
      DockerComposeActionResultModel res;
      if (action == 'up') {
        res = await dockerService.composeUp(
          currentWorkspaceId.value,
          currentServerId.value,
          projectId,
        );
      } else if (action == 'down') {
        res = await dockerService.composeDown(
          currentWorkspaceId.value,
          currentServerId.value,
          projectId,
        );
      } else {
        res = await dockerService.composeRestart(
          currentWorkspaceId.value,
          currentServerId.value,
          projectId,
        );
      }

      Get.snackbar(
        res.success ? 'Berhasil' : 'Aksi Gagal',
        res.message,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: res.success ? Colors.teal : Colors.red,
        colorText: Colors.white,
      );

      loadProjectStatus(projectId);
    } on ApiException catch (e) {
      Get.snackbar(
        'Aksi Gagal',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red.withValues(alpha: 0.85),
        colorText: Colors.white,
      );
    } finally {
      isActionLoading.value = false;
    }
  }

  void showComposeActionDialog({
    required BuildContext context,
    required String projectId,
    required String projectName,
    required String action,
  }) {
    final actionCapital = action.toUpperCase();
    final Color btnColor = action == 'down'
        ? Colors.redAccent
        : (action == 'restart' ? Colors.orangeAccent : Colors.tealAccent);

    Get.defaultDialog(
      title: 'Konfirmasi Compose $actionCapital',
      titleStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
      backgroundColor: const Color(0xFF1E293B),
      content: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8.0),
        child: Column(
          children: [
            Text(
              'Jalankan "docker compose $action" pada project:',
              style: const TextStyle(color: Colors.white70, fontSize: 13),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: Colors.white12),
              ),
              child: Text(
                projectName,
                style: const TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ),
          ],
        ),
      ),
      textConfirm: actionCapital,
      textCancel: 'Batal',
      confirmTextColor: Colors.black,
      buttonColor: btnColor,
      cancelTextColor: Colors.white60,
      onConfirm: () {
        Get.back();
        executeComposeAction(projectId, action);
      },
    );
  }
}
