import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/deployment_model.dart';
import '../../../data/services/deployment_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../app/theme/app_colors.dart';

class DeploymentController extends GetxController {
  final DeploymentService _deploymentService;

  DeploymentController({DeploymentService? deploymentService})
      : _deploymentService = deploymentService ?? Get.find<DeploymentService>();

  final RxList<DeploymentModel> deployments = <DeploymentModel>[].obs;
  final RxBool isLoading = false.obs;
  final RxBool isDeploying = false.obs;
  final RxString selectedStatus = 'ALL'.obs;
  final RxString errorMessage = ''.obs;

  // Selected deployment log state
  final Rx<DeploymentLogsModel?> currentLogs = Rx<DeploymentLogsModel?>(null);
  final RxBool isLoadingLogs = false.obs;
  final RxInt logLines = 100.obs;

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
      fetchDeployments();
    }
  }

  Future<void> fetchDeployments({bool showLoading = true}) async {
    if (workspaceId.isEmpty) return;
    if (showLoading) isLoading.value = true;
    errorMessage.value = '';

    try {
      final res = await _deploymentService.getDeployments(
        workspaceId,
        environmentId: environmentId,
        serverId: serverId,
        status: selectedStatus.value == 'ALL' ? null : selectedStatus.value,
        limit: 50,
      );
      deployments.assignAll(res);
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Gagal memuat riwayat deployment: $e';
    } finally {
      if (showLoading) isLoading.value = false;
    }
  }

  Future<void> refreshDeployments() async {
    await fetchDeployments(showLoading: false);
  }

  void filterStatus(String status) {
    selectedStatus.value = status;
    fetchDeployments();
  }

  Future<bool> triggerDeployment(
    DeploymentConfigModel config, {
    required bool confirm,
  }) async {
    if (isDeploying.value) return false;
    isDeploying.value = true;

    try {
      await _deploymentService.triggerDeployment(
        workspaceId,
        config.id,
        confirm: confirm,
      );

      Get.snackbar(
        'Deployment Dimulai',
        'Deployment untuk "${config.name}" sedang berjalan.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.success.withValues(alpha: 0.9),
        colorText: Colors.white,
        duration: const Duration(seconds: 4),
      );

      await refreshDeployments();
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Deployment Gagal',
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
        'Terjadi kesalahan saat memicu deployment: $e',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.error.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return false;
    } finally {
      isDeploying.value = false;
    }
  }

  Future<void> fetchLogs(String deploymentId, {int? lines}) async {
    isLoadingLogs.value = true;
    try {
      final res = await _deploymentService.getDeploymentLogs(
        workspaceId,
        deploymentId,
        lines: lines ?? logLines.value,
      );
      currentLogs.value = res;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Memuat Log', e.message);
    } catch (e) {
      Get.snackbar('Error Log', '$e');
    } finally {
      isLoadingLogs.value = false;
    }
  }
}
