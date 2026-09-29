import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import '../../../data/models/backup_model.dart';
import '../controllers/backup_controller.dart';
import 'backup_log_view.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/utils/formatters.dart';

class BackupDetailView extends StatelessWidget {
  final String workspaceId;
  final BackupModel backup;

  const BackupDetailView({
    super.key,
    required this.workspaceId,
    required this.backup,
  });

  void _copyToClipboard(String text, String label) {
    Clipboard.setData(ClipboardData(text: text));
    Get.snackbar(
      'Disalin',
      '$label berhasil disalin ke clipboard.',
      backgroundColor: AppColors.success.withValues(alpha: 0.9),
      colorText: Colors.white,
      snackPosition: SnackPosition.BOTTOM,
      duration: const Duration(seconds: 2),
    );
  }

  @override
  Widget build(BuildContext context) {
    final controller = Get.isRegistered<BackupController>()
        ? Get.find<BackupController>()
        : Get.put(BackupController());

    controller.workspaceId = workspaceId;

    return Scaffold(
      appBar: AppAppBar(
        title: 'Detail Backup',
        actions: [
          IconButton(
            icon: const Icon(Icons.description_outlined, color: Colors.white),
            tooltip: 'Lihat Log',
            onPressed: () {
              Get.to(() => BackupLogView(
                    workspaceId: workspaceId,
                    backup: backup,
                  ));
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Status Header Card
            AppCard(
              child: Column(
                children: [
                  _buildStatusIcon(backup.status),
                  const SizedBox(height: 12),
                  Text(
                    backup.status.toUpperCase(),
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: _getStatusColor(backup.status),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    backup.backupConfigName ?? 'Backup',
                    style: const TextStyle(
                      fontSize: 14,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // File & Storage Info
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Informasi Berkas Backup',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildInfoTile(
                    'Tipe Backup',
                    backup.backupType ?? 'POSTGRESQL',
                    icon: Icons.category_rounded,
                  ),
                  const Divider(height: 16, color: AppColors.border),
                  _buildInfoTile(
                    'Environment',
                    backup.environmentName ?? '-',
                    icon: Icons.cloud_outlined,
                  ),
                  const Divider(height: 16, color: AppColors.border),
                  _buildInfoTile(
                    'Server',
                    backup.serverName ?? '-',
                    icon: Icons.dns_outlined,
                  ),
                  if (backup.fileName != null) ...[
                    const Divider(height: 16, color: AppColors.border),
                    _buildInfoTile(
                      'Nama Berkas',
                      backup.fileName!,
                      icon: Icons.insert_drive_file_outlined,
                      isMonospace: true,
                    ),
                  ],
                  if (backup.filePath != null) ...[
                    const Divider(height: 16, color: AppColors.border),
                    _buildInfoTile(
                      'Lokasi Berkas',
                      backup.filePath!,
                      icon: Icons.folder_open_rounded,
                      isMonospace: true,
                    ),
                  ],
                  if (backup.fileSizeBytes != null) ...[
                    const Divider(height: 16, color: AppColors.border),
                    _buildInfoTile(
                      'Ukuran Berkas',
                      backup.formattedFileSize,
                      icon: Icons.data_usage_rounded,
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Checksum & Integrity Card
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Integritas & Checksum',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      if (backup.checksum != null)
                        IconButton(
                          icon: const Icon(Icons.copy_rounded, size: 18, color: AppColors.primary),
                          tooltip: 'Salin Checksum',
                          onPressed: () => _copyToClipboard(backup.checksum!, 'Checksum SHA-256'),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (backup.checksum != null) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.background,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'SHA-256',
                            style: TextStyle(
                              fontSize: 11,
                              color: AppColors.textSecondary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          SelectableText(
                            backup.checksum!,
                            style: const TextStyle(
                              fontSize: 12,
                              fontFamily: 'monospace',
                              color: AppColors.success,
                              height: 1.4,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ] else ...[
                    const Text(
                      'Checksum belum tersedia atau backup belum berhasil selesai.',
                      style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],

                  // Verification reactive result
                  Obx(() {
                    final verifyRes = controller.verifyResult.value;
                    if (verifyRes != null && verifyRes.backupId == backup.id) {
                      return Container(
                        margin: const EdgeInsets.only(top: 12),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: (verifyRes.verified ? AppColors.success : AppColors.error).withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: (verifyRes.verified ? AppColors.success : AppColors.error).withValues(alpha: 0.4),
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              verifyRes.verified ? Icons.check_circle_rounded : Icons.cancel_rounded,
                              color: verifyRes.verified ? AppColors.success : AppColors.error,
                              size: 20,
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                verifyRes.message,
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: verifyRes.verified ? AppColors.success : AppColors.error,
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    }
                    return const SizedBox.shrink();
                  }),

                  if (backup.isSuccess) ...[
                    const SizedBox(height: 16),
                    Obx(() => AppButton(
                          text: 'Verifikasi Berkas Backup',
                          icon: const Icon(Icons.verified_user_rounded, size: 18),
                          variant: AppButtonVariant.outline,
                          isLoading: controller.isVerifying.value,
                          onPressed: () => controller.verifyBackup(backup.id),
                        )),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Execution Timestamps Card
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Waktu Eksekusi',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildInfoTile(
                    'Dimulai',
                    AppFormatters.formatDateTime(backup.startedAt),
                    icon: Icons.play_arrow_outlined,
                  ),
                  const Divider(height: 16, color: AppColors.border),
                  _buildInfoTile(
                    'Selesai',
                    backup.finishedAt != null ? AppFormatters.formatDateTime(backup.finishedAt!) : '-',
                    icon: Icons.stop_outlined,
                  ),
                  const Divider(height: 16, color: AppColors.border),
                  _buildInfoTile(
                    'Durasi',
                    backup.durationFormatted,
                    icon: Icons.timer_outlined,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Action Buttons
            AppButton(
              text: 'Lihat Log Backup',
              icon: const Icon(Icons.terminal_rounded, size: 18),
              onPressed: () {
                Get.to(() => BackupLogView(
                      workspaceId: workspaceId,
                      backup: backup,
                    ));
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusIcon(String status) {
    IconData icon;
    Color color = _getStatusColor(status);

    switch (status.toUpperCase()) {
      case 'SUCCESS':
        icon = Icons.check_circle_rounded;
        break;
      case 'FAILED':
        icon = Icons.cancel_rounded;
        break;
      case 'RUNNING':
        icon = Icons.autorenew_rounded;
        break;
      default:
        icon = Icons.hourglass_empty_rounded;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        shape: BoxShape.circle,
      ),
      child: Icon(icon, color: color, size: 36),
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'SUCCESS':
        return AppColors.success;
      case 'FAILED':
        return AppColors.error;
      case 'RUNNING':
        return AppColors.primary;
      default:
        return AppColors.warning;
    }
  }

  Widget _buildInfoTile(String label, String value, {IconData? icon, bool isMonospace = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (icon != null) ...[
          Icon(icon, size: 16, color: AppColors.textSecondary),
          const SizedBox(width: 8),
        ],
        Text(
          label,
          style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontFamily: isMonospace ? 'monospace' : null,
              fontWeight: FontWeight.w600,
              color: Colors.white,
            ),
            textAlign: TextAlign.end,
          ),
        ),
      ],
    );
  }
}
