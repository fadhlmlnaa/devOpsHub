import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../controllers/notification_controller.dart';
import '../widgets/notification_tile.dart';
import 'alert_detail_view.dart';

class NotificationListView extends StatefulWidget {
  final String workspaceId;

  const NotificationListView({
    super.key,
    required this.workspaceId,
  });

  @override
  State<NotificationListView> createState() => _NotificationListViewState();
}

class _NotificationListViewState extends State<NotificationListView> {
  late NotificationController controller;

  @override
  void initState() {
    super.initState();
    controller = Get.find<NotificationController>();
    controller.initWorkspace(widget.workspaceId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(
          'Inbox Notifikasi',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        backgroundColor: AppColors.surface,
        elevation: 0,
        actions: [
          // Mark all read button
          IconButton(
            icon: const Icon(Icons.done_all_rounded, color: AppColors.primary),
            tooltip: 'Tandai Semua Dibaca',
            onPressed: () => controller.markAllAsRead(),
          ),
          // Preferences modal trigger
          IconButton(
            icon: const Icon(Icons.tune_outlined, color: AppColors.textPrimary),
            tooltip: 'Preferensi Notifikasi',
            onPressed: () => _showPreferencesBottomSheet(context),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await controller.fetchNotifications();
        },
        color: AppColors.primary,
        child: Column(
          children: [
            // Filter Bar: Unread only filter chip
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: AppColors.surface,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Obx(() => FilterChip(
                        label: Text(
                          controller.unreadOnly.value ? 'Hanya Belum Dibaca' : 'Semua Notifikasi',
                          style: TextStyle(
                            color: controller.unreadOnly.value ? AppColors.primary : AppColors.textSecondary,
                            fontSize: 12,
                            fontWeight: controller.unreadOnly.value ? FontWeight.bold : FontWeight.normal,
                          ),
                        ),
                        selected: controller.unreadOnly.value,
                        selectedColor: AppColors.primary.withValues(alpha: 0.2),
                        backgroundColor: AppColors.surfaceElevated,
                        checkmarkColor: AppColors.primary,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        side: BorderSide(
                          color: controller.unreadOnly.value ? AppColors.primary : AppColors.border,
                        ),
                        onSelected: (_) => controller.toggleUnreadOnly(),
                      )),
                  Obx(() {
                    final unread = controller.unreadCount.value;
                    if (unread <= 0) return const SizedBox.shrink();
                    return Text(
                      '$unread belum dibaca',
                      style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                    );
                  }),
                ],
              ),
            ),

            // Notification List
            Expanded(
              child: Obx(() {
                if (controller.isLoading.value) {
                  return const Center(child: CircularProgressIndicator(color: AppColors.primary));
                }

                if (controller.errorMessage.isNotEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.error_outline, size: 48, color: AppColors.error),
                          const SizedBox(height: 12),
                          Text(
                            controller.errorMessage.value,
                            style: const TextStyle(color: AppColors.textSecondary),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: () => controller.fetchNotifications(),
                            child: const Text('Coba Lagi'),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                final list = controller.notifications;
                if (list.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.notifications_off_outlined, size: 64, color: AppColors.textMuted.withValues(alpha: 0.5)),
                        const SizedBox(height: 12),
                        const Text(
                          'Tidak ada notifikasi',
                          style: TextStyle(color: AppColors.textSecondary, fontSize: 15, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Notifikasi operasional dan alert akan tampil di sini.',
                          style: TextStyle(color: AppColors.textMuted, fontSize: 13),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: list.length,
                  itemBuilder: (context, index) {
                    final notif = list[index];
                    return NotificationTile(
                      notification: notif,
                      onTap: () async {
                        if (!notif.isRead) {
                          await controller.markAsRead(notif.id);
                        }
                        if (notif.alertId != null && notif.alertId!.isNotEmpty) {
                          Get.to(() => AlertDetailView(
                                workspaceId: widget.workspaceId,
                                alertId: notif.alertId!,
                              ));
                        }
                      },
                    );
                  },
                );
              }),
            ),
          ],
        ),
      ),
    );
  }

  void _showPreferencesBottomSheet(BuildContext context) {
    final pref = controller.preferences.value;
    bool inApp = pref?.inAppEnabled ?? true;
    bool email = pref?.emailEnabled ?? false;
    String minSeverity = pref?.minimumSeverity ?? 'INFO';

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF161B22),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Preferensi Notifikasi',
                        style: TextStyle(color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: AppColors.textMuted),
                        onPressed: () => Navigator.of(context).pop(),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // In-App Switch
                  SwitchListTile(
                    title: const Text('In-App Notification', style: TextStyle(color: AppColors.textPrimary)),
                    subtitle: const Text('Tampilkan notifikasi di dalam aplikasi', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
                    value: inApp,
                    activeThumbColor: AppColors.primary,
                    contentPadding: EdgeInsets.zero,
                    onChanged: (val) => setModalState(() => inApp = val),
                  ),

                  // Email Switch
                  SwitchListTile(
                    title: const Text('Email Notification', style: TextStyle(color: AppColors.textPrimary)),
                    subtitle: const Text('Kirim email peringatan (jika server email aktif)', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
                    value: email,
                    activeThumbColor: AppColors.primary,
                    contentPadding: EdgeInsets.zero,
                    onChanged: (val) => setModalState(() => email = val),
                  ),

                  const SizedBox(height: 12),
                  const Text('Minimum Severity Peringatan:', style: TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),

                  Row(
                    children: ['INFO', 'WARNING', 'CRITICAL'].map((sev) {
                      final isSelected = minSeverity == sev;
                      Color color = AppColors.info;
                      if (sev == 'WARNING') color = AppColors.warning;
                      if (sev == 'CRITICAL') color = AppColors.error;

                      return Expanded(
                        child: GestureDetector(
                          onTap: () => setModalState(() => minSeverity = sev),
                          child: Container(
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            decoration: BoxDecoration(
                              color: isSelected ? color.withValues(alpha: 0.2) : AppColors.surfaceElevated,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: isSelected ? color : AppColors.border, width: isSelected ? 1.5 : 1),
                            ),
                            child: Center(
                              child: Text(
                                sev,
                                style: TextStyle(
                                  color: isSelected ? color : AppColors.textMuted,
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),

                  const SizedBox(height: 24),

                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: AppColors.textOnPrimary,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: () async {
                        Navigator.of(context).pop();
                        await controller.updatePreferences(
                          inAppEnabled: inApp,
                          emailEnabled: email,
                          minimumSeverity: minSeverity,
                        );
                      },
                      child: const Text('Simpan Pengaturan', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
