import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/backup_model.dart';
import '../../../data/services/backup_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../app/theme/app_colors.dart';

class BackupController extends GetxController {
  final BackupService _backupService;

  BackupController({BackupService? backupService})
      : _backupService = backupService ?? Get.find<BackupService>();

  final RxList<BackupModel> backups = <BackupModel>[].obs;
  final RxBool isLoading = false.obs;
  final RxBool isRunningBackup = false.obs;
  final RxBool isVerifying = false.obs;
  final RxString selectedType = 'ALL'.obs;
  final RxString selectedStatus = 'ALL'.obs;
  final RxString errorMessage = ''.obs;

  // Selected backup logs state
  final Rx<BackupLogsModel?> currentLogs = Rx<BackupLogsModel?>(null);
  final RxBool isLoadingLogs = false.obs;

  // Selected backup verify state
  final Rx<BackupVerifyResultModel?> verifyResult = Rx<BackupVerifyResultModel?>(null);

  late String workspaceId;
  String? environmentId;
  String? serverId;

  @override
  void onInit() {
    super.onInit();
    final args = Get.arguments;
    if (args is Map<String, dynamic>) {
      workspaceId = args['workspace_id']?.toString() ?? '';
      environmentId = args['environment_id']?.toString();
      serverId = args['server_id']?.toString();
    } else {
      workspaceId = '';
    }

    if (workspaceId.isNotEmpty) {
      fetchBackups();
    }
  }

  Future<void> fetchBackups({bool showLoading = true}) async {
    if (workspaceId.isEmpty) return;
    if (showLoading) isLoading.value = true;
    errorMessage.value = '';

    try {
      final res = await _backupService.getBackups(
        workspaceId,
        environmentId: environmentId,
        serverId: serverId,
        backupType: selectedType.value == 'ALL' ? null : selectedType.value,
        status: selectedStatus.value == 'ALL' ? null : selectedStatus.value,
        limit: 50,
      );
      backups.assignAll(res);
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Gagal memuat riwayat backup: $e';
    } finally {
      if (showLoading) isLoading.value = false;
    }
  }

  Future<void> refreshBackups() async {
    await fetchBackups(showLoading: false);
  }

  void filterByType(String type) {
    selectedType.value = type;
    fetchBackups();
  }

  void filterByStatus(String status) {
    selectedStatus.value = status;
    fetchBackups();
  }

  Future<bool> triggerBackup(
    BackupConfigModel config, {
    required bool confirm,
  }) async {
    if (isRunningBackup.value) return false;
    isRunningBackup.value = true;

    try {
      await _backupService.triggerBackup(
        workspaceId,
        config.id,
        confirm: confirm,
      );

      Get.snackbar(
        'Backup Dimulai',
        'Operasi backup untuk "${config.name}" sedang berjalan.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.success.withValues(alpha: 0.9),
        colorText: Colors.white,
        duration: const Duration(seconds: 4),
      );

      await refreshBackups();
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Backup Gagal',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.error.withValues(alpha: 0.9),
        colorText: Colors.white,
        duration: const Duration(seconds: 5),
      );
      return false;
    } catch (e) {
      Get.snackbar(
        'Kesalahan',
        'Terjadi kesalahan saat memicu backup: $e',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.error.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return false;
    } finally {
      isRunningBackup.value = false;
    }
  }

  Future<void> fetchLogs(String backupId, {int? lines}) async {
    isLoadingLogs.value = true;
    try {
      final res = await _backupService.getBackupLogs(
        workspaceId,
        backupId,
        lines: lines ?? 100,
      );
      currentLogs.value = res;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Memuat Log', e.message);
    } catch (e) {
      Get.snackbar('Error', '$e');
    } finally {
      isLoadingLogs.value = false;
    }
  }

  Future<BackupVerifyResultModel?> verifyBackup(String backupId) async {
    isVerifying.value = true;
    try {
      final res = await _backupService.verifyBackup(workspaceId, backupId);
      verifyResult.value = res;

      Get.snackbar(
        res.verified ? 'Verifikasi Sukses' : 'Verifikasi Gagal',
        res.message,
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: (res.verified ? AppColors.success : AppColors.error).withValues(alpha: 0.9),
        colorText: Colors.white,
        duration: const Duration(seconds: 4),
      );

      return res;
    } on ApiException catch (e) {
      Get.snackbar(
        'Verifikasi Gagal',
        e.message,
        backgroundColor: AppColors.error.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return null;
    } catch (e) {
      Get.snackbar('Error', '$e');
      return null;
    } finally {
      isVerifying.value = false;
    }
  }
}
