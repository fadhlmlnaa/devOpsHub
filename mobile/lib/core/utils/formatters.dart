import 'dart:math';

class AppFormatters {
  AppFormatters._();

  /// Formats bytes into human-readable string (B, KB, MB, GB, TB)
  static String formatBytes(int? bytes, {int decimals = 1}) {
    if (bytes == null || bytes <= 0) return '0 B';
    const suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    final i = (log(bytes) / log(1024)).floor();
    final clampedI = i.clamp(0, suffixes.length - 1);
    final size = bytes / pow(1024, clampedI);
    return '${size.toStringAsFixed(decimals)} ${suffixes[clampedI]}';
  }

  /// Formats percentage (0.0 - 100.0)
  static String formatPercentage(double? pct, {int decimals = 1}) {
    if (pct == null) return '-';
    return '${pct.toStringAsFixed(decimals)}%';
  }

  /// Formats uptime seconds into human-readable format, e.g. "18h 45m" or "2d 4h"
  static String formatUptime(int? seconds) {
    if (seconds == null || seconds <= 0) return 'Baru menyala';
    final days = seconds ~/ 86400;
    final hours = (seconds % 86400) ~/ 3600;
    final minutes = (seconds % 3600) ~/ 60;
    final sec = seconds % 60;

    final parts = <String>[];
    if (days > 0) parts.add('${days}d');
    if (hours > 0) parts.add('${hours}h');
    if (minutes > 0) parts.add('${minutes}m');
    if (parts.isEmpty) parts.add('${sec}s');

    return parts.join(' ');
  }

  /// Formats relative time from DateTime
  static String formatRelativeTime(DateTime? dateTime) {
    if (dateTime == null) return '-';
    final now = DateTime.now();
    final diff = now.difference(dateTime);

    if (diff.inSeconds < 45) {
      return 'Baru saja';
    } else if (diff.inMinutes < 60) {
      return '${diff.inMinutes}m lalu';
    } else if (diff.inHours < 24) {
      return '${diff.inHours}j lalu';
    } else {
      return '${diff.inDays}h lalu';
    }
  }

  /// Formats DateTime into 'DD/MM/YYYY HH:mm'
  static String formatDateTime(DateTime? dateTime) {
    if (dateTime == null) return '-';
    final d = dateTime.toLocal();
    final day = d.day.toString().padLeft(2, '0');
    final month = d.month.toString().padLeft(2, '0');
    final year = d.year.toString();
    final hour = d.hour.toString().padLeft(2, '0');
    final min = d.minute.toString().padLeft(2, '0');
    return '$day/$month/$year $hour:$min';
  }

  /// Formats DateTime into 'HH:mm:ss'
  static String formatTime(DateTime? dateTime) {
    if (dateTime == null) return '--:--';
    final d = dateTime.toLocal();
    final hour = d.hour.toString().padLeft(2, '0');
    final min = d.minute.toString().padLeft(2, '0');
    final sec = d.second.toString().padLeft(2, '0');
    return '$hour:$min:$sec';
  }
}

