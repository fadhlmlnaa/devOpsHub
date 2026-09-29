import 'package:flutter/material.dart';
import '../../../data/models/deployment_model.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/utils/formatters.dart';

class DeploymentCard extends StatelessWidget {
  final DeploymentModel deployment;
  final VoidCallback onTap;

  const DeploymentCard({
    super.key,
    required this.deployment,
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
              _buildStatusIcon(deployment.status),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      deployment.deploymentConfigName ?? 'Deployment',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${deployment.environmentName ?? 'Env'} • ${deployment.serverName ?? 'Server'}',
                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
              _buildStatusBadge(deployment.status),
            ],
          ),
          const SizedBox(height: 12),

          if (deployment.commitReference != null || deployment.triggeredByName != null) ...[
            Row(
              children: [
                if (deployment.commitReference != null) ...[
                  const Icon(Icons.commit_rounded, size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    deployment.commitReference!,
                    style: const TextStyle(
                      fontSize: 12,
                      fontFamily: 'monospace',
                      color: AppColors.primary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 12),
                ],
                if (deployment.triggeredByName != null) ...[
                  const Icon(Icons.person_outline_rounded, size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      deployment.triggeredByName!,
                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 8),
          ],

          if (deployment.message != null && deployment.message!.isNotEmpty) ...[
            Text(
              deployment.message!,
              style: TextStyle(
                fontSize: 12,
                color: deployment.isFailed ? AppColors.error : AppColors.textSecondary,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 8),
          ],

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                deployment.createdAt != null
                    ? AppFormatters.formatDateTime(deployment.createdAt!)
                    : '-',
                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
              ),
              const Row(
                children: [
                  Text(
                    'Lihat Log',
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

  Widget _buildStatusIcon(String status) {
    IconData icon;
    Color color;

    switch (status.toUpperCase()) {
      case 'SUCCESS':
        icon = Icons.check_circle_rounded;
        color = AppColors.success;
        break;
      case 'FAILED':
        icon = Icons.cancel_rounded;
        color = AppColors.error;
        break;
      case 'RUNNING':
        icon = Icons.autorenew_rounded;
        color = AppColors.primary;
        break;
      default:
        icon = Icons.hourglass_empty_rounded;
        color = AppColors.warning;
    }

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        shape: BoxShape.circle,
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
