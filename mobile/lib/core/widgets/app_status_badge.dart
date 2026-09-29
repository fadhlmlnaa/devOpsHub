import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';

class AppStatusBadge extends StatelessWidget {
  final String label;
  final Color? color;
  final Color? backgroundColor;
  final IconData? icon;

  const AppStatusBadge({
    super.key,
    required this.label,
    this.color,
    this.backgroundColor,
    this.icon,
  });

  factory AppStatusBadge.role(String role) {
    Color textColor;
    Color bgColor;

    switch (role.toUpperCase()) {
      case 'OWNER':
        textColor = AppColors.roleOwner;
        bgColor = AppColors.roleOwner.withValues(alpha: 0.12);
        break;
      case 'ADMIN':
        textColor = AppColors.roleAdmin;
        bgColor = AppColors.roleAdmin.withValues(alpha: 0.12);
        break;
      case 'DEVELOPER':
        textColor = AppColors.roleDeveloper;
        bgColor = AppColors.roleDeveloper.withValues(alpha: 0.12);
        break;
      case 'VIEWER':
      default:
        textColor = AppColors.roleViewer;
        bgColor = AppColors.roleViewer.withValues(alpha: 0.12);
        break;
    }

    return AppStatusBadge(
      label: role.toUpperCase(),
      color: textColor,
      backgroundColor: bgColor,
    );
  }

  factory AppStatusBadge.success(String label) {
    return AppStatusBadge(
      label: label,
      color: AppColors.success,
      backgroundColor: AppColors.successBg,
    );
  }

  factory AppStatusBadge.error(String label) {
    return AppStatusBadge(
      label: label,
      color: AppColors.error,
      backgroundColor: AppColors.errorBg,
    );
  }

  @override
  Widget build(BuildContext context) {
    final effectiveColor = color ?? AppColors.primary;
    final effectiveBg = backgroundColor ?? effectiveColor.withValues(alpha: 0.12);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: effectiveBg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: effectiveColor.withValues(alpha: 0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 12, color: effectiveColor),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: effectiveColor,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
