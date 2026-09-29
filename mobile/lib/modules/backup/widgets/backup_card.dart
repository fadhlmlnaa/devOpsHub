import 'package:flutter/material.dart';
import '../../../data/models/backup_model.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/utils/formatters.dart';

class BackupCard extends StatelessWidget {
  final BackupModel backup;
  final VoidCallback onTap;

  const BackupCard({
    super.key,
    required this.backup,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _buildTypeIcon(backup.backupType ?? 'POSTGRESQL'),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      backup.backupConfigName ?? backup.fileName ?? 'Backup',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${backup.environmentName ?? 'Env'} • ${backup.serverName ?? 'Server'}',
                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
              _buildStatusBadge(backup.status),
            ],
          ),
          const SizedBox(height: 12),

          if (backup.fileName != null) ...[
            Row(
              children: [
                const Icon(Icons.insert_drive_file_outlined, size: 14, color: AppColors.textSecondary),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    backup.fileName!,
                    style: const TextStyle(
                      fontSize: 12,
                      fontFamily: 'monospace',
                      color: AppColors.primary,
                      fontWeight: FontWeight.w600,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (backup.fileSizeBytes != null) ...[
                  const SizedBox(width: 8),
                  Text(
                    backup.formattedFileSize,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.white70,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 8),
          ],

          if (backup.checksum != null) ...[
            Row(
              children: [
                const Icon(Icons.verified_outlined, size: 14, color: AppColors.success),
                const SizedBox(width: 6),
                Text(
                  'SHA-256: ${backup.checksumSnippet}',
                  style: const TextStyle(
                    fontSize: 11,
                    fontFamily: 'monospace',
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
          ],

          if (backup.errorMessage != null && backup.errorMessage!.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: AppColors.error.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(
                children: [
                  const Icon(Icons.error_outline_rounded, size: 14, color: AppColors.error),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      backup.errorMessage!,
                      style: const TextStyle(fontSize: 11, color: AppColors.error),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
          ],

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                AppFormatters.formatDateTime(backup.startedAt),
                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
              ),
              const Row(
                children: [
                  Text(
                    'Detail',
                    style: TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(width: 4),
                  Icon(Icons.chevron_right_rounded, size: 16, color: AppColors.primary),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTypeIcon(String type) {
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
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: color, size: 20),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color bg;
    Color fg;

    switch (status.toUpperCase()) {
      case 'SUCCESS':
        bg = AppColors.success.withValues(alpha: 0.15);
        fg = AppColors.success;
        break;
      case 'FAILED':
        bg = AppColors.error.withValues(alpha: 0.15);
        fg = AppColors.error;
        break;
      case 'RUNNING':
        bg = AppColors.primary.withValues(alpha: 0.15);
        fg = AppColors.primary;
        break;
      default:
        bg = AppColors.warning.withValues(alpha: 0.15);
        fg = AppColors.warning;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(
          color: fg,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
