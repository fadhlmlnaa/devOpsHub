import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../controllers/alert_controller.dart';

class AlertDetailView extends StatefulWidget {
  final String workspaceId;
  final String alertId;

  const AlertDetailView({
    super.key,
    required this.workspaceId,
    required this.alertId,
  });

  @override
  State<AlertDetailView> createState() => _AlertDetailViewState();
}

class _AlertDetailViewState extends State<AlertDetailView> {
  late AlertController controller;

  @override
  void initState() {
    super.initState();
    controller = Get.find<AlertController>();
    controller.initWorkspace(widget.workspaceId);
    controller.loadAlertDetail(widget.alertId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Detail Alert', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        backgroundColor: AppColors.surface,
        elevation: 0,
      ),
      body: Obx(() {
        if (controller.isLoadingDetail.value) {
          return const Center(child: CircularProgressIndicator(color: AppColors.primary));
        }

        final alert = controller.selectedAlert.value;
        if (alert == null) {
          return const Center(
            child: Text('Alert tidak ditemukan', style: TextStyle(color: AppColors.textSecondary)),
          );
        }

        final isFiring = alert.isFiring;

        Color severityColor;
        Color severityBg;
        switch (alert.severity.toUpperCase()) {
          case 'CRITICAL':
            severityColor = AppColors.error;
            severityBg = AppColors.errorBg;
            break;
          case 'WARNING':
            severityColor = AppColors.warning;
            severityBg = AppColors.warningBg;
            break;
          default:
            severityColor = AppColors.info;
            severityBg = AppColors.infoBg;
        }

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.surfaceCard,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isFiring ? severityColor.withValues(alpha: 0.6) : AppColors.border,
                    width: isFiring ? 1.5 : 1,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        // Status Badge
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: isFiring ? AppColors.errorBg : AppColors.successBg,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                              color: isFiring ? AppColors.error : AppColors.success,
                            ),
                          ),
                          child: Text(
                            isFiring ? 'FIRING' : 'RESOLVED',
                            style: TextStyle(
                              color: isFiring ? AppColors.error : AppColors.success,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        // Severity Badge
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: severityBg,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            alert.severity.toUpperCase(),
                            style: TextStyle(
                              color: severityColor,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      alert.title,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (alert.message != null && alert.message!.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                        alert.message!,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Metric & Evaluation Information Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.surfaceCard,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Informasi Evaluasi',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    _buildInfoRow('Aturan Alert', alert.ruleName ?? alert.alertRuleId),
                    _buildInfoRow('Tipe Metrik', alert.metricType ?? '-'),
                    _buildInfoRow('Server Target', alert.serverName ?? 'Semua Server'),
                    _buildInfoRow('Environment', alert.environmentName ?? 'Workspace-wide'),
                    if (alert.currentValue != null)
                      _buildInfoRow('Nilai Terdeteksi', '${alert.currentValue?.toStringAsFixed(1)}'),
                    if (alert.thresholdValue != null)
                      _buildInfoRow('Nilai Batas (Threshold)', '${alert.thresholdValue?.toStringAsFixed(1)}'),
                    if (alert.triggeredAt != null)
                      _buildInfoRow('Waktu Terpicu', AppFormatters.formatDateTime(alert.triggeredAt!)),
                    if (alert.resolvedAt != null)
                      _buildInfoRow('Waktu Selesai', AppFormatters.formatDateTime(alert.resolvedAt!)),
                    if (alert.lastEvaluatedAt != null)
                      _buildInfoRow('Evaluasi Terakhir', AppFormatters.formatDateTime(alert.lastEvaluatedAt!)),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Audit Events Timeline
              const Text(
                'Audit Trail Riwayat Event',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 10),

              Obx(() {
                final events = controller.alertEvents;
                if (events.isEmpty) {
                  return Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceCard,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Text(
                      'Belum ada riwayat event audit.',
                      style: TextStyle(color: AppColors.textMuted, fontSize: 13),
                    ),
                  );
                }

                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceCard,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: events.length,
                    separatorBuilder: (context, index) => const Divider(color: AppColors.divider, height: 20),
                    itemBuilder: (context, index) {
                      final event = events[index];
                      Color dotColor = AppColors.primary;
                      if (event.eventType == 'TRIGGERED') dotColor = AppColors.error;
                      if (event.eventType == 'RESOLVED') dotColor = AppColors.success;
                      if (event.eventType == 'NOTIFICATION_SENT') dotColor = AppColors.info;

                      return Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            margin: const EdgeInsets.only(top: 5),
                            decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      event.eventType,
                                      style: TextStyle(
                                        color: dotColor,
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    if (event.createdAt != null)
                                      Text(
                                        AppFormatters.formatRelativeTime(event.createdAt!),
                                        style: const TextStyle(
                                          color: AppColors.textMuted,
                                          fontSize: 11,
                                        ),
                                      ),
                                  ],
                                ),
                                if (event.message != null && event.message!.isNotEmpty) ...[
                                  const SizedBox(height: 4),
                                  Text(
                                    event.message!,
                                    style: const TextStyle(
                                      color: AppColors.textSecondary,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ],
                      );
                    },
                  ),
                );
              }),

              const SizedBox(height: 24),

              // Manual Resolve Action Button (if Firing)
              if (isFiring)
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.success,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    icon: const Icon(Icons.check_circle_outline),
                    label: const Text(
                      'Selesaikan Alert Secara Manual',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    onPressed: () => _showResolveConfirmationDialog(),
                  ),
                ),
            ],
          ),
        );
      }),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
          Flexible(
            child: Text(
              value,
              style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w500),
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ),
    );
  }

  void _showResolveConfirmationDialog() {
    Get.dialog(
      AlertDialog(
        backgroundColor: AppColors.surfaceElevated,
        title: const Text('Selesaikan Alert Manual?', style: TextStyle(color: AppColors.textPrimary)),
        content: const Text(
          'Alert akan diubah ke status RESOLVED. Aturan monitoring tetap aktif, dan alert dapat menyala kembali jika metrik masih di atas batas pada siklus evaluasi berikutnya.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Batal', style: TextStyle(color: AppColors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.success),
            onPressed: () async {
              Get.back();
              await controller.resolveAlert(widget.alertId);
            },
            child: const Text('Konfirmasi Selesai', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
