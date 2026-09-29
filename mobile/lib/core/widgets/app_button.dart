import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';

enum AppButtonVariant { primary, outline, text, danger }

class AppButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final Widget? icon;
  final AppButtonVariant variant;
  final double? width;
  final double height;
  final EdgeInsetsGeometry? padding;

  const AppButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.icon,
    this.variant = AppButtonVariant.primary,
    this.width,
    this.height = 48,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveOnPressed = isLoading ? null : onPressed;

    Widget buttonContent = Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (isLoading) ...[
          SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(
                variant == AppButtonVariant.primary
                    ? AppColors.textOnPrimary
                    : AppColors.primary,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Text(
            'Memproses...',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: variant == AppButtonVariant.primary
                  ? AppColors.textOnPrimary
                  : AppColors.primary,
            ),
          ),
        ] else ...[
          if (icon != null) ...[
            icon!,
            const SizedBox(width: 8),
          ],
          Text(
            text,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: _getTextColor(),
            ),
          ),
        ],
      ],
    );

    Widget buttonWidget;

    switch (variant) {
      case AppButtonVariant.primary:
        buttonWidget = Container(
          decoration: BoxDecoration(
            gradient: effectiveOnPressed != null
                ? AppColors.primaryGradient
                : null,
            color: effectiveOnPressed == null ? AppColors.surfaceElevated : null,
            borderRadius: BorderRadius.circular(12),
          ),
          child: ElevatedButton(
            onPressed: effectiveOnPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.transparent,
              shadowColor: Colors.transparent,
              disabledBackgroundColor: Colors.transparent,
              foregroundColor: AppColors.textOnPrimary,
              padding: padding ?? const EdgeInsets.symmetric(horizontal: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: buttonContent,
          ),
        );
        break;

      case AppButtonVariant.outline:
        buttonWidget = OutlinedButton(
          onPressed: effectiveOnPressed,
          style: OutlinedButton.styleFrom(
            side: BorderSide(
              color: effectiveOnPressed == null
                  ? AppColors.border
                  : AppColors.borderFocused,
            ),
            padding: padding ?? const EdgeInsets.symmetric(horizontal: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          child: buttonContent,
        );
        break;

      case AppButtonVariant.text:
        buttonWidget = TextButton(
          onPressed: effectiveOnPressed,
          style: TextButton.styleFrom(
            foregroundColor: AppColors.primary,
            padding: padding ?? const EdgeInsets.symmetric(horizontal: 12),
          ),
          child: buttonContent,
        );
        break;

      case AppButtonVariant.danger:
        buttonWidget = ElevatedButton(
          onPressed: effectiveOnPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.error,
            foregroundColor: Colors.white,
            padding: padding ?? const EdgeInsets.symmetric(horizontal: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          child: buttonContent,
        );
        break;
    }

    return SizedBox(
      width: width ?? double.infinity,
      height: height,
      child: buttonWidget,
    );
  }

  Color _getTextColor() {
    if (onPressed == null) return AppColors.textDisabled;
    switch (variant) {
      case AppButtonVariant.primary:
        return AppColors.textOnPrimary;
      case AppButtonVariant.outline:
      case AppButtonVariant.text:
        return AppColors.primary;
      case AppButtonVariant.danger:
        return Colors.white;
    }
  }
}
