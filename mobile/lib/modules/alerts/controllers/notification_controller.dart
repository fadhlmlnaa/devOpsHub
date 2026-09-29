import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/alert_model.dart';
import '../../../data/services/alert_service.dart';
import '../../../core/network/api_exception.dart';

class NotificationController extends GetxController {
  final AlertService alertService;

  NotificationController({required this.alertService});

  final RxList<NotificationModel> notifications = <NotificationModel>[].obs;
  final RxInt unreadCount = 0.obs;
  final RxBool isLoading = false.obs;
  final RxBool unreadOnly = false.obs;
  final RxString errorMessage = ''.obs;

  // Preferences
  final Rx<NotificationPreferenceModel?> preferences = Rx<NotificationPreferenceModel?>(null);
  final RxBool isSavingPreferences = false.obs;

  String? currentWorkspaceId;

  void initWorkspace(String workspaceId) {
    currentWorkspaceId = workspaceId;
    fetchUnreadCount();
    fetchNotifications();
    fetchPreferences();
  }

  Future<void> fetchUnreadCount() async {
    if (currentWorkspaceId == null) return;
    try {
      final res = await alertService.getUnreadNotificationCount(currentWorkspaceId!);
      unreadCount.value = res.unreadCount;
    } catch (_) {
      // Background polling or silent fetch
    }
  }

  Future<void> fetchNotifications({bool showLoading = true}) async {
    if (currentWorkspaceId == null) return;
    if (showLoading) isLoading.value = true;
    errorMessage.value = '';

    try {
      final list = await alertService.getNotifications(
        currentWorkspaceId!,
        unreadOnly: unreadOnly.value ? true : null,
      );
      notifications.assignAll(list);
      await fetchUnreadCount();
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Gagal memuat notifikasi: $e';
    } finally {
      if (showLoading) isLoading.value = false;
    }
  }

  void toggleUnreadOnly() {
    unreadOnly.value = !unreadOnly.value;
    fetchNotifications();
  }

  Future<void> markAsRead(String notificationId) async {
    if (currentWorkspaceId == null) return;
    try {
      final updated = await alertService.markNotificationRead(currentWorkspaceId!, notificationId);
      final index = notifications.indexWhere((n) => n.id == notificationId);
      if (index != -1) {
        notifications[index] = updated;
      }
      if (unreadCount.value > 0) {
        unreadCount.value -= 1;
      }
    } catch (e) {
      Get.snackbar('Error', 'Gagal menandai notifikasi dibaca: $e');
    }
  }

  Future<void> markAllAsRead() async {
    if (currentWorkspaceId == null) return;
    try {
      await alertService.markAllNotificationsRead(currentWorkspaceId!);
      unreadCount.value = 0;
      await fetchNotifications(showLoading: false);
      Get.snackbar(
        'Berhasil',
        'Semua notifikasi ditandai telah dibaca.',
        backgroundColor: Colors.teal.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
    } catch (e) {
      Get.snackbar('Error', 'Gagal menandai semua notifikasi: $e');
    }
  }

  Future<void> fetchPreferences() async {
    if (currentWorkspaceId == null) return;
    try {
      final pref = await alertService.getNotificationPreferences(currentWorkspaceId!);
      preferences.value = pref;
    } catch (_) {}
  }

  Future<bool> updatePreferences({
    required bool inAppEnabled,
    required bool emailEnabled,
    required String minimumSeverity,
  }) async {
    if (currentWorkspaceId == null) return false;
    isSavingPreferences.value = true;
    try {
      final updated = await alertService.updateNotificationPreferences(
        currentWorkspaceId!,
        {
          'in_app_enabled': inAppEnabled,
          'email_enabled': emailEnabled,
          'minimum_severity': minimumSeverity,
        },
      );
      preferences.value = updated;
      Get.snackbar(
        'Preferensi Disimpan',
        'Pengaturan notifikasi berhasil diperbarui.',
        backgroundColor: Colors.green.withValues(alpha: 0.8),
        colorText: Colors.white,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Simpan Preferensi', e.message, backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
      return false;
    } catch (e) {
      Get.snackbar('Error', 'Terjadi kesalahan: $e', backgroundColor: Colors.red.withValues(alpha: 0.8), colorText: Colors.white);
      return false;
    } finally {
      isSavingPreferences.value = false;
    }
  }
}
