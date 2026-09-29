import 'package:flutter/material.dart';
import '../../../data/models/deployment_model.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_button.dart';

class DeploymentConfigCard extends StatelessWidget {
  final DeploymentConfigModel config;
  final VoidCallback onDeploy;
  final VoidCallback onEdit;
  final VoidCallback onDelete;
  final bool isDeploying;

  const DeploymentConfigCard({
    super.key,
    required this.config,
    required this.onDeploy,
    required this.onEdit,
    required this.onDelete,
    this.isDeploying = false,
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
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: (isProtected ? AppColors.error : AppColors.primary).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  config.isDockerCompose ? Icons.layers_rounded : Icons.terminal_rounded,
                  color: isProtected ? AppColors.error : AppColors.primary,
                  size: 24,
                ),
              ),
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
                      'App: ${config.applicationName} • ${config.deploymentType}',
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
              if (config.branch != null) _buildBadge(Icons.call_split_rounded, config.branch!),
            ],
          ),
          const SizedBox(height: 8),

          Text(
            'Path: ${config.workingDirectory}',
            style: const TextStyle(
              fontSize: 11,
              fontFamily: 'monospace',
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 16),

          // Action button
          AppButton(
            text: 'Deploy Sekarang',
            icon: const Icon(Icons.rocket_launch_rounded, size: 18),
            isLoading: isDeploying,
            onPressed: onDeploy,
          ),
        ],
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
