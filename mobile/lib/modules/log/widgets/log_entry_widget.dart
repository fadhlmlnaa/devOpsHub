import 'package:flutter/material.dart';
import '../../../data/models/log_model.dart';

class LogEntryWidget extends StatelessWidget {
  final LogEntryModel entry;
  final int lineNumber;
  final bool showLineNumber;
  final bool showTimestamp;
  final bool wrap;
  final VoidCallback onCopy;

  const LogEntryWidget({
    super.key,
    required this.entry,
    required this.lineNumber,
    this.showLineNumber = true,
    this.showTimestamp = true,
    this.wrap = true,
    required this.onCopy,
  });

  Color _getPriorityColor(String priority) {
    switch (priority.toUpperCase()) {
      case 'EMERGENCY':
      case 'ALERT':
      case 'CRITICAL':
      case 'ERROR':
        return const Color(0xFFFF7B72); // Bright Terminal Red
      case 'WARNING':
        return const Color(0xFFFFA657); // Terminal Amber
      case 'NOTICE':
      case 'INFO':
        return const Color(0xFF7EE787); // Terminal Green
      case 'DEBUG':
        return const Color(0xFFD2A8FF); // Terminal Purple
      default:
        return const Color(0xFF8B949E); // Terminal Gray
    }
  }

  String _formatTimeOnly(DateTime dt) {
    final hh = dt.hour.toString().padLeft(2, '0');
    final mm = dt.minute.toString().padLeft(2, '0');
    final ss = dt.second.toString().padLeft(2, '0');
    return '$hh:$mm:$ss';
  }

  @override
  Widget build(BuildContext context) {
    final color = _getPriorityColor(entry.priority);
    final timeStr = entry.timestamp != null && showTimestamp
        ? _formatTimeOnly(entry.timestamp!)
        : null;

    final isError = entry.priority.toUpperCase() == 'ERROR' ||
        entry.priority.toUpperCase() == 'CRITICAL' ||
        entry.priority.toUpperCase() == 'EMERGENCY';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: isError
            ? const Color(0xFFFF7B72).withValues(alpha: 0.07)
            : Colors.transparent,
        border: Border(
          bottom: BorderSide(
            color: Colors.white.withValues(alpha: 0.03),
            width: 0.5,
          ),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Line Number
          if (showLineNumber)
            Container(
              width: 38,
              alignment: Alignment.topRight,
              padding: const EdgeInsets.only(right: 8),
              child: Text(
                '$lineNumber',
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 11,
                  color: Color(0xFF484F58),
                  height: 1.45,
                ),
              ),
            ),

          // 2. Timestamp
          if (timeStr != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Text(
                timeStr,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 11,
                  color: Color(0xFF79C0FF),
                  height: 1.45,
                ),
              ),
            ),

          // 3. Priority Tag
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Text(
              '[${entry.priority.toUpperCase().substring(0, entry.priority.length > 4 ? 4 : entry.priority.length)}]',
              style: TextStyle(
                fontFamily: 'monospace',
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: color,
                height: 1.45,
              ),
            ),
          ),

          // 4. Message Content
          Expanded(
            child: InkWell(
              onLongPress: onCopy,
              child: SelectableText(
                entry.message,
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: isError ? const Color(0xFFFFDCD7) : const Color(0xFFE6EDF3),
                  height: 1.45,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

