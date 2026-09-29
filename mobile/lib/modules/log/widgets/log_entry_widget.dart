import 'package:flutter/material.dart';
import '../../../data/models/log_model.dart';

class LogEntryWidget extends StatelessWidget {
  final LogEntryModel entry;
  final VoidCallback onCopy;

  const LogEntryWidget({
    super.key,
    required this.entry,
    required this.onCopy,
  });

  Color _getPriorityColor(String priority) {
    switch (priority.toUpperCase()) {
      case 'EMERGENCY':
      case 'ALERT':
      case 'CRITICAL':
      case 'ERROR':
        return Colors.redAccent;
      case 'WARNING':
      case 'NOTICE':
        return Colors.amberAccent;
      case 'INFO':
        return Colors.tealAccent;
      case 'DEBUG':
        return Colors.blueGrey;
      default:
        return Colors.white54;
    }
  }

  String _formatDateTime(DateTime dt) {
    final y = dt.year.toString().padLeft(4, '0');
    final m = dt.month.toString().padLeft(2, '0');
    final d = dt.day.toString().padLeft(2, '0');
    final hh = dt.hour.toString().padLeft(2, '0');
    final mm = dt.minute.toString().padLeft(2, '0');
    final ss = dt.second.toString().padLeft(2, '0');
    return '$y-$m-$d $hh:$mm:$ss';
  }

  @override
  Widget build(BuildContext context) {
    final color = _getPriorityColor(entry.priority);
    final timeStr = entry.timestamp != null ? _formatDateTime(entry.timestamp!) : null;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: entry.priority.toUpperCase() == 'ERROR' ||
                  entry.priority.toUpperCase() == 'CRITICAL'
              ? Colors.redAccent.withValues(alpha: 0.3)
              : Colors.white.withValues(alpha: 0.06),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Priority tag
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: color.withValues(alpha: 0.4)),
                ),
                child: Text(
                  entry.priority.toUpperCase(),
                  style: TextStyle(
                    color: color,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              if (timeStr != null)
                Text(
                  timeStr,
                  style: const TextStyle(
                    color: Colors.white38,
                    fontSize: 11,
                    fontFamily: 'monospace',
                  ),
                ),
              const Spacer(),
              InkWell(
                borderRadius: BorderRadius.circular(4),
                onTap: onCopy,
                child: const Padding(
                  padding: EdgeInsets.all(4),
                  child: Icon(
                    Icons.copy_rounded,
                    size: 14,
                    color: Colors.white38,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Monospace Message
          SelectableText(
            entry.message,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontFamily: 'monospace',
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}
