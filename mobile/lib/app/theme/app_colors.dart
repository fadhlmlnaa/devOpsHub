import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // Brand Palette based on DevOpsHub Logo
  static const Color background = Color(0xFF071E1B);
  static const Color surface = Color(0xFF0B2925);
  static const Color surfaceElevated = Color(0xFF0F3630);
  static const Color surfaceCard = Color(0xFF133F39);
  
  // Borders & Dividers
  static const Color border = Color(0xFF1B4E46);
  static const Color borderFocused = Color(0xFF00D2FF);
  static const Color divider = Color(0xFF154039);

  // Primary Brand Accents
  static const Color primary = Color(0xFF00D2FF);
  static const Color primaryLight = Color(0xFF6AE3FF);
  static const Color primaryDark = Color(0xFF00A3C7);
  
  // Secondary / Gradient Accents
  static const Color accentCyan = Color(0xFF00F2FE);
  static const Color accentMint = Color(0xFF20DFB7);
  static const Color accentBlue = Color(0xFF4FACFE);

  // Gradient definitions
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFF00D2FF), Color(0xFF0091FF)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient logoGradient = LinearGradient(
    colors: [Color(0xFF38E1FF), Color(0xFF20DFB7)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient surfaceGradient = LinearGradient(
    colors: [Color(0xFF0B2925), Color(0xFF071E1B)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  // Text Colors
  static const Color textPrimary = Color(0xFFF1F5F9);
  static const Color textSecondary = Color(0xFF94A8A4);
  static const Color textMuted = Color(0xFF5D7B76);
  static const Color textDisabled = Color(0xFF405753);
  static const Color textOnPrimary = Color(0xFF041B18);

  // Feedback & Status Colors
  static const Color success = Color(0xFF10B981);
  static const Color successBg = Color(0xFF063326);
  static const Color warning = Color(0xFFF59E0B);
  static const Color warningBg = Color(0xFF382606);
  static const Color error = Color(0xFFEF4444);
  static const Color errorBg = Color(0xFF381111);
  static const Color info = Color(0xFF3B82F6);
  static const Color infoBg = Color(0xFF0B2545);

  // Role Badges
  static const Color roleOwner = Color(0xFF00D2FF);
  static const Color roleAdmin = Color(0xFFA78BFA);
  static const Color roleDeveloper = Color(0xFF34D399);
  static const Color roleViewer = Color(0xFF94A3B8);
}
