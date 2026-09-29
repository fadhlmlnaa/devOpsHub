import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/deployment_model.dart';
import '../../../data/services/deployment_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../app/theme/app_colors.dart';

class DeploymentConfigController extends GetxController {
  final DeploymentService _deploymentService;

  DeploymentConfigController({DeploymentService? deploymentService})
      : _deploymentService = deploymentService ?? Get.find<DeploymentService>();

  final RxList<DeploymentConfigModel> configs = <DeploymentConfigModel>[].obs;
  final RxBool isLoading = false.obs;
  final RxBool isSubmitting = false.obs;
  final RxString errorMessage = ''.obs;

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
      fetchConfigs();
    }
  }

  Future<void> fetchConfigs({bool showLoading = true}) async {
    if (workspaceId.isEmpty) return;
    if (showLoading) isLoading.value = true;
    errorMessage.value = '';

    try {
      final res = await _deploymentService.getDeploymentConfigs(
        workspaceId,
        environmentId: environmentId,
        serverId: serverId,
      );
      configs.assignAll(res);
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Gagal memuat konfigurasi deployment: $e';
    } finally {
      if (showLoading) isLoading.value = false;
    }
  }

  Future<void> refreshConfigs() async {
    await fetchConfigs(showLoading: false);
  }

  Future<bool> createConfig(Map<String, dynamic> payload) async {
    isSubmitting.value = true;
    try {
      final res = await _deploymentService.createDeploymentConfig(workspaceId, payload);
      configs.add(res);
      Get.snackbar(
        'Berhasil',
        'Konfigurasi deployment "${res.name}" berhasil disimpan.',
        backgroundColor: AppColors.success.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Menyimpan',
        e.message,
        backgroundColor: AppColors.error.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return false;
    } catch (e) {
      Get.snackbar('Error', '$e');
      return false;
    } finally {
      isSubmitting.value = false;
    }
  }

  Future<bool> updateConfig(String configId, Map<String, dynamic> payload) async {
    isSubmitting.value = true;
    try {
      final res = await _deploymentService.updateDeploymentConfig(workspaceId, configId, payload);
      final idx = configs.indexWhere((c) => c.id == configId);
      if (idx != -1) {
        configs[idx] = res;
      }
      Get.snackbar(
        'Berhasil Diperbarui',
        'Konfigurasi deployment berhasil diperbarui.',
        backgroundColor: AppColors.success.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Memperbarui',
        e.message,
        backgroundColor: AppColors.error.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return false;
    } catch (e) {
      Get.snackbar('Error', '$e');
      return false;
    } finally {
      isSubmitting.value = false;
    }
  }

  Future<bool> deleteConfig(String configId) async {
    try {
      await _deploymentService.deleteDeploymentConfig(workspaceId, configId);
      configs.removeWhere((c) => c.id == configId);
      Get.snackbar(
        'Berhasil Dihapus',
        'Konfigurasi deployment telah dihapus.',
        backgroundColor: AppColors.success.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Menghapus',
        e.message,
        backgroundColor: AppColors.error.withValues(alpha: 0.9),
        colorText: Colors.white,
      );
      return false;
    } catch (e) {
      Get.snackbar('Error', '$e');
      return false;
    }
  }
}
