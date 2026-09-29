import 'package:flutter/material.dart';
import '../../../app/theme/app_colors.dart';
import '../../../data/models/alert_model.dart';
import '../../../core/utils/formatters.dart';

class NotificationTile extends StatelessWidget {
  final NotificationModel notification;
  final VoidCallback onTap;

  const NotificationTile({
    super.key,
    required this.notification,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color severityColor;
    Color severityBg;
    IconData icon;

    switch (notification.severity.toUpperCase()) {
      case 'CRITICAL':
        severityColor = AppColors.error;
        severityBg = AppColors.errorBg;
        icon = Icons.error_outline;
        break;
      case 'WARNING':
        severityColor = AppColors.warning;
        severityBg = AppColors.warningBg;
        icon = Icons.warning_amber_rounded;
        break;
      default:
        severityColor = AppColors.info;
        severityBg = AppColors.infoBg;
        icon = Icons.notifications_none_rounded;
    }

    final isRead = notification.isRead;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: isRead ? AppColors.surfaceElevated.withValues(alpha: 0.4) : AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isRead ? AppColors.border.withValues(alpha: 0.3) : AppColors.primary.withValues(alpha: 0.3),
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Severity icon badge
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: severityBg,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: severityColor, size: 20),
              ),
              const SizedBox(width: 12),

              // Title and message
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            notification.title,
                            style: TextStyle(
                              color: isRead ? AppColors.textSecondary : AppColors.textPrimary,
                              fontSize: 14,
                              fontWeight: isRead ? FontWeight.w500 : FontWeight.bold,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (notification.createdAt != null)
                          Text(
                            AppFormatters.formatRelativeTime(notification.createdAt!),
                            style: const TextStyle(
                              color: AppColors.textMuted,
                              fontSize: 11,
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      notification.message,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),

              // Unread blue dot indicator
              if (!isRead) ...[
                const SizedBox(width: 8),
                Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.only(top: 4),
                  decoration: const BoxDecoration(
                    color: AppColors.primary,
                    shape: BoxShape.circle,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
