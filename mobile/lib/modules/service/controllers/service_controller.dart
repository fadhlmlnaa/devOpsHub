import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/service_model.dart';
import '../../../data/services/service_service.dart';

class ServiceController extends GetxController {
  final ServiceService serviceService;

  ServiceController({required this.serviceService});

  final RxBool isLoading = false.obs;
  final RxBool isActionLoading = false.obs;
  final RxString actionLoadingName = ''.obs;
  final RxString actionType = ''.obs;

  final RxBool systemdSupported = true.obs;
  final RxList<ServiceModel> services = <ServiceModel>[].obs;
  final Rxn<ServiceModel> selectedService = Rxn<ServiceModel>();

  final RxString activeFilter = 'all'.obs;
  final RxString searchQuery = ''.obs;
  final RxString errorMessage = ''.obs;

  final RxString currentWorkspaceId = ''.obs;
  final RxString currentServerId = ''.obs;
  final RxString currentServerName = ''.obs;
  final RxString currentUserRole = 'VIEWER'.obs;

  bool get canMutate {
    final role = currentUserRole.value.toUpperCase();
    return role == 'OWNER' || role == 'ADMIN';
  }

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
    loadServices();
  }

  List<ServiceModel> get filteredServices {
    var list = services.toList();

    // Filter by tab
    if (activeFilter.value == 'active') {
      list = list.where((s) => s.isRunning).toList();
    } else if (activeFilter.value == 'inactive') {
      list = list.where((s) => s.isStopped).toList();
    } else if (activeFilter.value == 'failed') {
      list = list.where((s) => s.isFailed).toList();
    }

    // Filter by search query
    final q = searchQuery.value.trim().toLowerCase();
    if (q.isNotEmpty) {
      list = list.where((s) {
        final nameMatch = s.name.toLowerCase().contains(q);
        final descMatch = s.description?.toLowerCase().contains(q) ?? false;
        return nameMatch || descMatch;
      }).toList();
    }

    return list;
  }

  void setFilter(String filter) {
    activeFilter.value = filter;
  }

  void setSearch(String query) {
    searchQuery.value = query;
  }

  Future<void> loadServices({bool silent = false}) async {
    if (currentWorkspaceId.value.isEmpty || currentServerId.value.isEmpty) return;

    if (!silent) {
      isLoading.value = true;
      errorMessage.value = '';
    }

    try {
      final res = await serviceService.getServices(
        currentWorkspaceId.value,
        currentServerId.value,
        state: activeFilter.value == 'all' ? null : activeFilter.value,
        limit: 200,
      );

      systemdSupported.value = res.systemdSupported;
      services.assignAll(res.services);

      if (!res.systemdSupported && res.message != null) {
        errorMessage.value = res.message!;
      }
    } on ApiException catch (e) {
      errorMessage.value = e.message;
      if (!silent) {
        Get.snackbar(
          'Gagal Memuat Services',
          e.message,
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.red.withValues(alpha: 0.8),
          colorText: Colors.white,
        );
      }
    } catch (e) {
      errorMessage.value = 'Terjadi kesalahan saat memuat daftar service.';
    } finally {
      if (!silent) {
        isLoading.value = false;
      }
    }
  }

  Future<void> loadServiceDetail(String serviceName) async {
    if (currentWorkspaceId.value.isEmpty || currentServerId.value.isEmpty) return;

    isLoading.value = true;
    try {
      final detail = await serviceService.getService(
        currentWorkspaceId.value,
        currentServerId.value,
        serviceName,
      );
      selectedService.value = detail;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Memuat Detail',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
    } catch (e) {
      Get.snackbar(
        'Kesalahan',
        'Gagal mengambil detail status service.',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> confirmAndExecuteAction({
    required BuildContext context,
    required String serviceName,
    required String action, // start, stop, restart, reload
  }) async {
    if (!canMutate) {
      Get.snackbar(
        'Akses Ditolak',
        'Hanya OWNER atau ADMIN yang diizinkan mengelola service.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.orange.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return;
    }

    String title = '';
    String desc = '';
    Color confirmColor = Colors.teal;

    switch (action.toLowerCase()) {
      case 'start':
        title = 'Nyalakan $serviceName?';
        desc = 'Aksi ini akan menjalankan service pada server ${currentServerName.value}.';
        confirmColor = Colors.green;
        break;
      case 'stop':
        title = 'Hentikan $serviceName?';
        desc = 'PERINGATAN: Menghentikan service dapat memutus aplikasi atau database yang sedang berjalan!';
        confirmColor = Colors.red;
        break;
      case 'restart':
        title = 'Restart $serviceName?';
        desc = 'Aksi ini akan memuat ulang proses service pada server ${currentServerName.value}.';
        confirmColor = Colors.orange;
        break;
      case 'reload':
        title = 'Reload Konfigurasi $serviceName?';
        desc = 'Aksi ini akan memuat ulang konfigurasi tanpa menghentikan service.';
        confirmColor = Colors.teal;
        break;
      default:
        title = 'Jalankan $action?';
        desc = 'Apakah Anda yakin ingin menjalankan aksi ini?';
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(
          title,
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
        ),
        content: Text(
          desc,
          style: const TextStyle(color: Colors.white70, fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Batal', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: confirmColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(
              action.toUpperCase(),
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _executeServiceAction(serviceName, action);
    }
  }

  Future<void> _executeServiceAction(String serviceName, String action) async {
    isActionLoading.value = true;
    actionLoadingName.value = serviceName;
    actionType.value = action;

    try {
      ServiceActionResultModel result;
      switch (action.toLowerCase()) {
        case 'start':
          result = await serviceService.startService(
            currentWorkspaceId.value,
            currentServerId.value,
            serviceName,
          );
          break;
        case 'stop':
          result = await serviceService.stopService(
            currentWorkspaceId.value,
            currentServerId.value,
            serviceName,
          );
          break;
        case 'restart':
          result = await serviceService.restartService(
            currentWorkspaceId.value,
            currentServerId.value,
            serviceName,
          );
          break;
        case 'reload':
          result = await serviceService.reloadService(
            currentWorkspaceId.value,
            currentServerId.value,
            serviceName,
          );
          break;
        default:
          throw ApiException(message: 'Aksi service tidak dikenal.');
      }

      if (result.success) {
        Get.snackbar(
          'Berhasil',
          result.message,
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.green.withValues(alpha: 0.85),
          colorText: Colors.white,
          duration: const Duration(seconds: 3),
        );
      } else {
        Get.snackbar(
          'Operasi Gagal',
          result.message,
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.red.withValues(alpha: 0.85),
          colorText: Colors.white,
          duration: const Duration(seconds: 4),
        );
      }

      // Refresh detail and list
      await loadServiceDetail(serviceName);
      await loadServices(silent: true);
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Eksekusi',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red.withValues(alpha: 0.85),
        colorText: Colors.white,
      );
    } catch (e) {
      Get.snackbar(
        'Kesalahan',
        'Terjadi kesalahan saat memproses aksi service.',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isActionLoading.value = false;
      actionLoadingName.value = '';
      actionType.value = '';
    }
  }
}
