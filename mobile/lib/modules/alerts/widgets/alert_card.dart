import 'package:flutter/material.dart';
import '../../../app/theme/app_colors.dart';
import '../../../data/models/alert_model.dart';
import '../../../core/utils/formatters.dart';

class AlertCard extends StatelessWidget {
  final AlertModel alert;
  final VoidCallback onTap;

  const AlertCard({
    super.key,
    required this.alert,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color severityColor;
    Color severityBg;
    IconData severityIcon;

    switch (alert.severity.toUpperCase()) {
      case 'CRITICAL':
        severityColor = AppColors.error;
        severityBg = AppColors.errorBg;
        severityIcon = Icons.error_outline;
        break;
      case 'WARNING':
        severityColor = AppColors.warning;
        severityBg = AppColors.warningBg;
        severityIcon = Icons.warning_amber_rounded;
        break;
      default:
        severityColor = AppColors.info;
        severityBg = AppColors.infoBg;
        severityIcon = Icons.info_outline;
    }

    final isFiring = alert.isFiring;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isFiring ? severityColor.withValues(alpha: 0.5) : AppColors.border,
          width: isFiring ? 1.5 : 1,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header: Status badge & Severity badge
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: isFiring ? AppColors.errorBg : AppColors.successBg,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                            color: isFiring ? AppColors.error : AppColors.success,
                            width: 1,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 6,
                              height: 6,
                              decoration: BoxDecoration(
                                color: isFiring ? AppColors.error : AppColors.success,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              isFiring ? 'FIRING' : 'RESOLVED',
                              style: TextStyle(
                                color: isFiring ? AppColors.error : AppColors.success,
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: severityBg,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(severityIcon, size: 12, color: severityColor),
                            const SizedBox(width: 4),
                            Text(
                              alert.severity.toUpperCase(),
                              style: TextStyle(
                                color: severityColor,
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  if (alert.triggeredAt != null)
                    Text(
                      AppFormatters.formatRelativeTime(alert.triggeredAt!),
                      style: const TextStyle(
                        color: AppColors.textMuted,
                        fontSize: 12,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),

              // Title
              Text(
                alert.title,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                ),
              ),

              if (alert.message != null && alert.message!.isNotEmpty) ...[
                const SizedBox(height: 6),
                Text(
                  alert.message!,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],

              const SizedBox(height: 12),
              const Divider(color: AppColors.divider, height: 1),
              const SizedBox(height: 10),

              // Footer: Target info (Server / Env) and values
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.dns_outlined, size: 14, color: AppColors.textMuted),
                      const SizedBox(width: 6),
                      Text(
                        alert.serverName ?? alert.environmentName ?? 'Workspace-wide',
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                  if (alert.currentValue != null && alert.thresholdValue != null)
                    Text(
                      'Nilai: ${alert.currentValue?.toStringAsFixed(1)} (Batas: ${alert.thresholdValue?.toStringAsFixed(1)})',
                      style: const TextStyle(
                        color: AppColors.textMuted,
                        fontSize: 11,
                        fontFamily: 'monospace',
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
