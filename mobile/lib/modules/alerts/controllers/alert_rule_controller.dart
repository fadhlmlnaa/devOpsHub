import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/alert_model.dart';
import '../../../data/services/alert_service.dart';
import '../../../core/network/api_exception.dart';

class AlertRuleController extends GetxController {
  final AlertService alertService;

  AlertRuleController({required this.alertService});

  final RxList<AlertRuleModel> rules = <AlertRuleModel>[].obs;
  final RxBool isLoading = false.obs;
  final RxBool isSubmitting = false.obs;
  final RxString errorMessage = ''.obs;

  String? currentWorkspaceId;
  String? currentServerId;

  void initWorkspace(String workspaceId, {String? serverId}) {
    currentWorkspaceId = workspaceId;
    currentServerId = serverId;
    fetchRules();
  }

  Future<void> fetchRules({bool showLoading = true}) async {
    if (currentWorkspaceId == null) return;
    if (showLoading) isLoading.value = true;
    errorMessage.value = '';

    try {
      final list = await alertService.getAlertRules(
        currentWorkspaceId!,
        serverId: currentServerId,
      );
      rules.assignAll(list);
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Gagal memuat aturan alert: $e';
    } finally {
      if (showLoading) isLoading.value = false;
    }
  }

  Future<bool> createRule(Map<String, dynamic> data) async {
    if (currentWorkspaceId == null) return false;
    isSubmitting.value = true;
    try {
      final created = await alertService.createAlertRule(currentWorkspaceId!, data);
      rules.insert(0, created);
      Get.snackbar(
        'Berhasil',
        'Aturan alert "${created.name}" berhasil dibuat.',
        backgroundColor: Colors.green.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Membuat Aturan', e.message, backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
      return false;
    } catch (e) {
      Get.snackbar('Error', 'Terjadi kesalahan: $e', backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
      return false;
    } finally {
      isSubmitting.value = false;
    }
  }

  Future<bool> updateRule(String ruleId, Map<String, dynamic> data) async {
    if (currentWorkspaceId == null) return false;
    isSubmitting.value = true;
    try {
      final updated = await alertService.updateAlertRule(currentWorkspaceId!, ruleId, data);
      final index = rules.indexWhere((r) => r.id == ruleId);
      if (index != -1) {
        rules[index] = updated;
      }
      Get.snackbar(
        'Berhasil',
        'Aturan alert "${updated.name}" berhasil diperbarui.',
        backgroundColor: Colors.green.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Update Aturan', e.message, backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
      return false;
    } catch (e) {
      Get.snackbar('Error', 'Terjadi kesalahan: $e', backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
      return false;
    } finally {
      isSubmitting.value = false;
    }
  }

  Future<void> toggleRuleStatus(AlertRuleModel rule) async {
    if (currentWorkspaceId == null) return;
    try {
      final updated = await alertService.updateAlertRule(
        currentWorkspaceId!,
        rule.id,
        {'is_enabled': !rule.isEnabled},
      );
      final index = rules.indexWhere((r) => r.id == rule.id);
      if (index != -1) {
        rules[index] = updated;
      }
    } on ApiException catch (e) {
      Get.snackbar('Gagal Mengubah Status', e.message, backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
    } catch (e) {
      Get.snackbar('Error', 'Terjadi kesalahan: $e', backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
    }
  }

  Future<bool> deleteRule(String ruleId) async {
    if (currentWorkspaceId == null) return false;
    try {
      await alertService.deleteAlertRule(currentWorkspaceId!, ruleId);
      rules.removeWhere((r) => r.id == ruleId);
      Get.snackbar(
        'Dihapus',
        'Aturan alert berhasil dihapus.',
        backgroundColor: Colors.orange.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Menghapus', e.message, backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
      return false;
    } catch (e) {
      Get.snackbar('Error', 'Terjadi kesalahan: $e', backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
      return false;
    }
  }
}
