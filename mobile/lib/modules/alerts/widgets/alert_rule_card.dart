import 'package:flutter/material.dart';
import '../../../app/theme/app_colors.dart';
import '../../../data/models/alert_model.dart';

class AlertRuleCard extends StatelessWidget {
  final AlertRuleModel rule;
  final ValueChanged<bool>? onToggleEnabled;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  const AlertRuleCard({
    super.key,
    required this.rule,
    this.onToggleEnabled,
    required this.onEdit,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    Color severityColor;
    Color severityBg;

    switch (rule.severity.toUpperCase()) {
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

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: rule.isEnabled ? AppColors.border : AppColors.border.withValues(alpha: 0.5),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Row 1: Name and Enabled Switch
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    rule.name,
                    style: TextStyle(
                      color: rule.isEnabled ? AppColors.textPrimary : AppColors.textMuted,
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Transform.scale(
                  scale: 0.8,
                  child: Switch(
                    value: rule.isEnabled,
                    activeThumbColor: AppColors.primary,
                    activeTrackColor: AppColors.primary.withValues(alpha: 0.3),
                    inactiveThumbColor: AppColors.textMuted,
                    inactiveTrackColor: AppColors.surfaceElevated,
                    onChanged: onToggleEnabled != null ? (v) => onToggleEnabled!(v) : null,
                  ),
                ),
                PopupMenuButton<String>(
                  icon: const Icon(Icons.more_vert, size: 20, color: AppColors.textMuted),
                  color: AppColors.surfaceElevated,
                  onSelected: (value) {
                    if (value == 'edit') onEdit();
                    if (value == 'delete') onDelete();
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'edit',
                      child: Row(
                        children: [
                          Icon(Icons.edit_outlined, size: 16, color: AppColors.primary),
                          SizedBox(width: 8),
                          Text('Edit Aturan', style: TextStyle(color: AppColors.textPrimary)),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete_outline, size: 16, color: AppColors.error),
                          SizedBox(width: 8),
                          Text('Hapus Aturan', style: TextStyle(color: AppColors.error)),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),

            if (rule.description != null && rule.description!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                rule.description!,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                ),
              ),
            ],

            const SizedBox(height: 12),

            // Chips: Condition, Duration, Severity, Scope
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                // Metric & Condition
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceElevated,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.analytics_outlined, size: 12, color: AppColors.primary),
                      const SizedBox(width: 4),
                      Text(
                        '${rule.metricTypeFormatted}: ${rule.conditionText}',
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),

                // Duration
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceElevated,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.timer_outlined, size: 12, color: AppColors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        rule.durationFormatted,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),

                // Severity
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: severityBg,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    rule.severity.toUpperCase(),
                    style: TextStyle(
                      color: severityColor,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),
            const Divider(color: AppColors.divider, height: 1),
            const SizedBox(height: 8),

            // Target Scope
            Row(
              children: [
                const Icon(Icons.location_on_outlined, size: 13, color: AppColors.textMuted),
                const SizedBox(width: 4),
                Text(
                  rule.serverName != null
                      ? 'Server: ${rule.serverName}'
                      : (rule.environmentName != null
                          ? 'Environment: ${rule.environmentName}'
                          : 'Workspace-wide (Semua Server)'),
                  style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
