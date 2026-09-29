import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/docker_model.dart';
import '../../../data/services/docker_service.dart';

class DockerController extends GetxController {
  final DockerService dockerService;

  DockerController({required this.dockerService});

  // State Observables
  final RxBool isLoading = false.obs;
  final RxBool isActionLoading = false.obs;
  final RxString errorMessage = ''.obs;

  final Rxn<DockerStatusModel> dockerStatus = Rxn<DockerStatusModel>();
  final RxList<DockerContainerModel> containers = <DockerContainerModel>[].obs;
  final Rxn<DockerContainerDetailModel> containerDetail = Rxn<DockerContainerDetailModel>();

  final RxString selectedStateFilter = 'running'.obs; // running, stopped, all
  final RxString searchQuery = ''.obs;

  final RxString currentWorkspaceId = ''.obs;
  final RxString currentServerId = ''.obs;
  final RxString currentServerName = ''.obs;
  final RxString currentUserRole = 'VIEWER'.obs;

  bool get canMutate =>
      currentUserRole.value.toUpperCase() == 'OWNER' ||
      currentUserRole.value.toUpperCase() == 'ADMIN';

  void initContext({
    required String workspaceId,
    required String serverId,
    String serverName = '',
    String userRole = 'VIEWER',
  }) {
    currentWorkspaceId.value = workspaceId;
    currentServerId.value = serverId;
    currentServerName.value = serverName;
    currentUserRole.value = userRole;
    loadDockerDashboard();
  }

  List<DockerContainerModel> get filteredContainers {
    final list = containers.toList();
    final q = searchQuery.value.trim().toLowerCase();
    if (q.isEmpty) return list;

    return list.where((c) {
      final nameMatch = c.name.toLowerCase().contains(q);
      final imageMatch = c.image.toLowerCase().contains(q);
      final idMatch = c.id.toLowerCase().contains(q);
      return nameMatch || imageMatch || idMatch;
    }).toList();
  }

  void setStateFilter(String state) {
    if (selectedStateFilter.value == state) return;
    selectedStateFilter.value = state;
    loadContainers(silent: false);
  }

  void setSearch(String query) {
    searchQuery.value = query;
  }

  Future<void> loadDockerDashboard({bool silent = false}) async {
    if (currentWorkspaceId.value.isEmpty || currentServerId.value.isEmpty) return;

    if (!silent) {
      isLoading.value = true;
      errorMessage.value = '';
    }

    try {
      final statusRes = await dockerService.getDockerStatus(
        currentWorkspaceId.value,
        currentServerId.value,
      );
      dockerStatus.value = statusRes;

      if (statusRes.isRunning) {
        final containersRes = await dockerService.getContainers(
          currentWorkspaceId.value,
          currentServerId.value,
          state: selectedStateFilter.value,
        );
        containers.assignAll(containersRes);
      } else {
        containers.clear();
      }
    } on ApiException catch (e) {
      errorMessage.value = e.message;
      if (!silent) {
        Get.snackbar(
          'Gagal Memuat Docker',
          e.message,
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.red.withValues(alpha: 0.85),
          colorText: Colors.white,
        );
      }
    } catch (e) {
      errorMessage.value = 'Terjadi kesalahan saat memeriksa Docker daemon.';
    } finally {
      if (!silent) {
        isLoading.value = false;
      }
    }
  }

  Future<void> loadContainers({bool silent = false}) async {
    if (currentWorkspaceId.value.isEmpty || currentServerId.value.isEmpty) return;

    if (!silent) isLoading.value = true;
    try {
      final res = await dockerService.getContainers(
        currentWorkspaceId.value,
        currentServerId.value,
        state: selectedStateFilter.value,
      );
      containers.assignAll(res);
    } catch (e) {
      // Ignored on silent refresh
    } finally {
      if (!silent) isLoading.value = false;
    }
  }

  Future<void> loadContainerDetail(String containerId) async {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      final res = await dockerService.getContainerDetail(
        currentWorkspaceId.value,
        currentServerId.value,
        containerId,
      );
      containerDetail.value = res;
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Gagal memuat detail container.';
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> executeContainerAction(String containerId, String action) async {
    if (!canMutate) {
      Get.snackbar(
        'Akses Ditolak',
        'Role ${currentUserRole.value} tidak memiliki izin untuk memodifikasi container.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.orange.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return;
    }

    isActionLoading.value = true;
    try {
      DockerContainerActionResultModel res;
      if (action == 'start') {
        res = await dockerService.startContainer(
          currentWorkspaceId.value,
          currentServerId.value,
          containerId,
        );
      } else if (action == 'stop') {
        res = await dockerService.stopContainer(
          currentWorkspaceId.value,
          currentServerId.value,
          containerId,
        );
      } else {
        res = await dockerService.restartContainer(
          currentWorkspaceId.value,
          currentServerId.value,
          containerId,
        );
      }

      Get.snackbar(
        res.success ? 'Berhasil' : 'Aksi Gagal',
        res.message,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: res.success ? Colors.teal : Colors.red,
        colorText: Colors.white,
      );

      // Refresh detail and dashboard list
      loadContainerDetail(containerId);
      loadContainers(silent: true);
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

  void showActionConfirmationDialog({
    required BuildContext context,
    required String containerId,
    required String containerName,
    required String action,
  }) {
    final actionCapital = action.toUpperCase();
    final Color btnColor = action == 'stop'
        ? Colors.redAccent
        : (action == 'restart' ? Colors.orangeAccent : Colors.tealAccent);

    Get.defaultDialog(
      title: 'Konfirmasi $actionCapital',
      titleStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
      backgroundColor: const Color(0xFF1E293B),
      content: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8.0),
        child: Column(
          children: [
            Text(
              'Apakah Anda yakin ingin melakukan $actionCapital pada container:',
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
                containerName,
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
        executeContainerAction(containerId, action);
      },
    );
  }
}
