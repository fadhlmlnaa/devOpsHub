import 'package:flutter/material.dart';
import '../../../data/models/backup_model.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_button.dart';

class BackupConfigCard extends StatelessWidget {
  final BackupConfigModel config;
  final VoidCallback onRun;
  final VoidCallback onEdit;
  final VoidCallback onDelete;
  final bool isRunning;

  const BackupConfigCard({
    super.key,
    required this.config,
    required this.onRun,
    required this.onEdit,
    required this.onDelete,
    this.isRunning = false,
  });

  @override
  Widget build(BuildContext context) {
    final isProtected = config.environmentIsProtected;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildTypeIcon(config.backupType, isProtected),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            config.name,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        if (isProtected)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppColors.error.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: AppColors.error.withValues(alpha: 0.4)),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.shield_rounded, color: AppColors.error, size: 12),
                                SizedBox(width: 4),
                                Text(
                                  'PROD',
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.error,
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Tipe: ${config.backupTypeFormatted} • ${config.isCompressed ? "Kompresi ON" : "Tanpa Kompresi"}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert_rounded, color: AppColors.textSecondary),
                color: AppColors.surfaceCard,
                onSelected: (val) {
                  if (val == 'edit') onEdit();
                  if (val == 'delete') onDelete();
                },
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'edit',
                    child: Row(
                      children: [
                        Icon(Icons.edit_outlined, size: 18, color: Colors.white),
                        SizedBox(width: 8),
                        Text('Edit Konfigurasi', style: TextStyle(color: Colors.white, fontSize: 13)),
                      ],
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'delete',
                    child: Row(
                      children: [
                        Icon(Icons.delete_outline_rounded, size: 18, color: AppColors.error),
                        SizedBox(width: 8),
                        Text('Hapus', style: TextStyle(color: AppColors.error, fontSize: 13)),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Details Chip Row
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              _buildBadge(Icons.cloud_outlined, config.environmentName ?? 'Env'),
              _buildBadge(Icons.dns_outlined, config.serverName ?? 'Server'),
              _buildBadge(Icons.history_toggle_off_rounded, '${config.retentionDays} Hari Retensi'),
            ],
          ),
          const SizedBox(height: 10),

          // Source and Destination
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.background,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Text('Sumber: ', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                    Expanded(
                      child: Text(
                        config.source,
                        style: const TextStyle(
                          fontSize: 11,
                          fontFamily: 'monospace',
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Text('Tujuan: ', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                    Expanded(
                      child: Text(
                        config.destination,
                        style: const TextStyle(
                          fontSize: 11,
                          fontFamily: 'monospace',
                          color: AppColors.primary,
                          fontWeight: FontWeight.w600,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Action button
          AppButton(
            text: 'Jalankan Backup',
            icon: const Icon(Icons.play_arrow_rounded, size: 18),
            isLoading: isRunning,
            onPressed: onRun,
          ),
        ],
      ),
    );
  }

  Widget _buildTypeIcon(String type, bool isProtected) {
    IconData icon;
    Color color;

    switch (type.toUpperCase()) {
      case 'POSTGRESQL':
        icon = Icons.storage_rounded;
        color = const Color(0xFF336791);
        break;
      case 'FILESYSTEM':
        icon = Icons.folder_zip_rounded;
        color = Colors.amber;
        break;
      case 'DOCKER_VOLUME':
        icon = Icons.layers_rounded;
        color = const Color(0xFF0db7ed);
        break;
      default:
        icon = Icons.cloud_download_rounded;
        color = AppColors.primary;
    }

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Icon(
        icon,
        color: color,
        size: 24,
      ),
    );
  }

  Widget _buildBadge(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: AppColors.textSecondary),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }
}
