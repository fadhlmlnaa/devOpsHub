import 'package:flutter/material.dart';

class ServiceActionButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isEnabled;

  const ServiceActionButton({
    super.key,
    required this.label,
    required this.icon,
    required this.color,
    required this.onPressed,
    this.isLoading = false,
    this.isEnabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveEnabled = isEnabled && !isLoading && onPressed != null;

    return Opacity(
      opacity: effectiveEnabled ? 1.0 : 0.45,
      child: Material(
        color: effectiveEnabled ? color.withValues(alpha: 0.15) : Colors.white.withValues(alpha: 0.04),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(
            color: effectiveEnabled ? color.withValues(alpha: 0.4) : Colors.white.withValues(alpha: 0.08),
          ),
        ),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: effectiveEnabled ? onPressed : null,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (isLoading)
                  SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(color),
                    ),
                  )
                else
                  Icon(
                    icon,
                    size: 18,
                    color: effectiveEnabled ? color : Colors.white54,
                  ),
                const SizedBox(width: 8),
                Text(
                  label,
                  style: TextStyle(
                    color: effectiveEnabled ? Colors.white : Colors.white54,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
