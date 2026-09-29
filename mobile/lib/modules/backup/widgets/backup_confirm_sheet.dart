import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/backup_model.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_button.dart';

class BackupConfirmSheet extends StatelessWidget {
  final BackupConfigModel config;
  final VoidCallback onConfirm;
  final bool isLoading;

  const BackupConfirmSheet({
    super.key,
    required this.config,
    required this.onConfirm,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    final isProtected = config.environmentIsProtected;

    return Container(
      decoration: const BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Row(
            children: [
              Icon(
                isProtected ? Icons.warning_amber_rounded : Icons.backup_rounded,
                color: isProtected ? AppColors.error : AppColors.primary,
                size: 28,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Konfirmasi Backup',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          if (isProtected) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.error.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.error.withValues(alpha: 0.4)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.shield_rounded, color: AppColors.error, size: 20),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'PERINGATAN: Environment ini bertipe PROTECTED / PRODUCTION. Operasi backup memerlukan konfirmasi eksplisit.',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppColors.error,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Config Specs
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.background,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              children: [
                _buildInfoRow('Backup', config.name),
                const Divider(height: 16, color: AppColors.border),
                _buildInfoRow('Tipe', config.backupTypeFormatted),
                const Divider(height: 16, color: AppColors.border),
                _buildInfoRow('Environment', config.environmentName ?? '-'),
                const Divider(height: 16, color: AppColors.border),
                _buildInfoRow('Server Target', config.serverName ?? '-'),
                const Divider(height: 16, color: AppColors.border),
                _buildInfoRow('Sumber', config.source),
                const Divider(height: 16, color: AppColors.border),
                _buildInfoRow('Tujuan', config.destination),
                const Divider(height: 16, color: AppColors.border),
                _buildInfoRow('Kompresi', config.isCompressed ? 'Ya (gzip/tgz)' : 'Tidak'),
                const Divider(height: 16, color: AppColors.border),
                _buildInfoRow('Retensi', '${config.retentionDays} Hari'),
              ],
            ),
          ),
          const SizedBox(height: 24),

          Row(
            children: [
              Expanded(
                child: AppButton(
                  text: 'Batal',
                  variant: AppButtonVariant.outline,
                  onPressed: () => Get.back(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: AppButton(
                  text: isProtected ? 'Ya, Jalankan (Prod)' : 'Ya, Jalankan Backup',
                  variant: isProtected ? AppButtonVariant.danger : AppButtonVariant.primary,
                  isLoading: isLoading,
                  onPressed: onConfirm,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
        ),
        const SizedBox(width: 12),
        Flexible(
          child: Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: Colors.white,
            ),
            textAlign: TextAlign.end,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
