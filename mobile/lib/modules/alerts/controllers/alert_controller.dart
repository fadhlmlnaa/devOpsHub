import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/alert_model.dart';
import '../../../data/services/alert_service.dart';
import '../../../core/network/api_exception.dart';

class AlertController extends GetxController {
  final AlertService alertService;

  AlertController({required this.alertService});

  final RxList<AlertModel> alerts = <AlertModel>[].obs;
  final RxBool isLoading = false.obs;
  final RxBool isEvaluating = false.obs;
  final RxString errorMessage = ''.obs;

  // Selected filters
  final RxString selectedStatus = 'ALL'.obs; // ALL, FIRING, RESOLVED
  final RxString selectedSeverity = 'ALL'.obs; // ALL, CRITICAL, WARNING, INFO
  final RxString searchQuery = ''.obs;

  // Detail view state
  final Rx<AlertModel?> selectedAlert = Rx<AlertModel?>(null);
  final RxList<AlertEventModel> alertEvents = <AlertEventModel>[].obs;
  final RxBool isLoadingDetail = false.obs;

  String? currentWorkspaceId;
  String? currentServerId;

  void initWorkspace(String workspaceId, {String? serverId}) {
    currentWorkspaceId = workspaceId;
    currentServerId = serverId;
    fetchAlerts();
  }

  Future<void> fetchAlerts({bool showLoading = true}) async {
    if (currentWorkspaceId == null) return;
    if (showLoading) isLoading.value = true;
    errorMessage.value = '';

    try {
      final list = await alertService.getAlerts(
        currentWorkspaceId!,
        status: selectedStatus.value,
        severity: selectedSeverity.value,
        serverId: currentServerId,
      );
      alerts.assignAll(list);
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Gagal memuat daftar alert: $e';
    } finally {
      if (showLoading) isLoading.value = false;
    }
  }

  void setStatusFilter(String status) {
    selectedStatus.value = status;
    fetchAlerts();
  }

  void setSeverityFilter(String severity) {
    selectedSeverity.value = severity;
    fetchAlerts();
  }

  void setSearchQuery(String query) {
    searchQuery.value = query;
  }

  List<AlertModel> get filteredAlerts {
    if (searchQuery.isEmpty) return alerts;
    final q = searchQuery.value.toLowerCase();
    return alerts.where((a) {
      final title = a.title.toLowerCase();
      final msg = (a.message ?? '').toLowerCase();
      final srv = (a.serverName ?? '').toLowerCase();
      final env = (a.environmentName ?? '').toLowerCase();
      return title.contains(q) || msg.contains(q) || srv.contains(q) || env.contains(q);
    }).toList();
  }

  int get firingCount => alerts.where((a) => a.isFiring).length;
  int get criticalCount => alerts.where((a) => a.isFiring && a.isCritical).length;

  Future<void> loadAlertDetail(String alertId) async {
    if (currentWorkspaceId == null) return;
    isLoadingDetail.value = true;
    try {
      final detail = await alertService.getAlertDetail(currentWorkspaceId!, alertId);
      selectedAlert.value = detail;
      final events = await alertService.getAlertEvents(currentWorkspaceId!, alertId);
      alertEvents.assignAll(events);
    } catch (e) {
      Get.snackbar(
        'Error',
        'Gagal memuat detail alert: $e',
        backgroundColor: Colors.red.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
    } finally {
      isLoadingDetail.value = false;
    }
  }

  Future<bool> resolveAlert(String alertId) async {
    if (currentWorkspaceId == null) return false;
    try {
      final resolved = await alertService.resolveAlert(currentWorkspaceId!, alertId, confirm: true);
      selectedAlert.value = resolved;
      // Refresh list
      final index = alerts.indexWhere((a) => a.id == alertId);
      if (index != -1) {
        alerts[index] = resolved;
      }
      // Refresh events
      final events = await alertService.getAlertEvents(currentWorkspaceId!, alertId);
      alertEvents.assignAll(events);

      Get.snackbar(
        'Berhasil',
        'Alert berhasil diselesaikan secara manual.',
        backgroundColor: Colors.green.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Menyelesaikan Alert',
        e.message,
        backgroundColor: Colors.red.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
      return false;
    } catch (e) {
      Get.snackbar(
        'Error',
        'Terjadi kesalahan: $e',
        backgroundColor: Colors.red.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
      return false;
    }
  }

  Future<void> triggerManualEvaluation() async {
    if (currentWorkspaceId == null) return;
    isEvaluating.value = true;
    try {
      final result = await alertService.evaluateAlerts(currentWorkspaceId!);
      final triggered = result['alerts_triggered'] ?? 0;
      final resolved = result['alerts_resolved'] ?? 0;
      Get.snackbar(
        'Evaluasi Selesai',
        'Dievaluasi: $triggered baru, $resolved terselesaikan.',
        backgroundColor: Colors.teal.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
      await fetchAlerts(showLoading: false);
    } on ApiException catch (e) {
      Get.snackbar('Gagal Evaluasi', e.message, backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
    } catch (e) {
      Get.snackbar('Error', 'Gagal evaluasi alert: $e', backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
    } finally {
      isEvaluating.value = false;
    }
  }
}
