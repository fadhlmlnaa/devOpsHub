import 'package:flutter/material.dart';
import '../../../data/models/docker_model.dart';

class DockerStatusCard extends StatelessWidget {
  final DockerStatusModel? status;
  final VoidCallback onRefresh;

  const DockerStatusCard({
    super.key,
    required this.status,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    if (status == null) {
      return const SizedBox.shrink();
    }

    final isRunning = status!.isRunning;
    final isStopped = status!.isStopped;

    Color badgeColor = Colors.grey;
    String badgeText = status!.state;
    IconData statusIcon = Icons.help_outline_rounded;

    if (isRunning) {
      badgeColor = const Color(0xFF27C93F); // Terminal Green
      badgeText = 'RUNNING';
      statusIcon = Icons.check_circle_rounded;
    } else if (isStopped) {
      badgeColor = const Color(0xFFFF5F56); // Red
      badgeText = 'DAEMON STOPPED';
      statusIcon = Icons.error_rounded;
    } else if (status!.isNotInstalled) {
      badgeColor = const Color(0xFF8B949E);
      badgeText = 'NOT INSTALLED';
      statusIcon = Icons.cancel_rounded;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isRunning
              ? const Color(0xFF27C93F).withValues(alpha: 0.25)
              : Colors.white10,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF58A6FF).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.directions_boat_rounded, color: Color(0xFF58A6FF), size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Docker Engine Daemon',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    Text(
                      status!.version != null ? 'Version: ${status!.version}' : 'Versi tidak terdeteksi',
                      style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: Colors.white60),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: badgeColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: badgeColor.withValues(alpha: 0.4)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(statusIcon, size: 12, color: badgeColor),
                    const SizedBox(width: 4),
                    Text(
                      badgeText,
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: badgeColor,
                        fontFamily: 'monospace',
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
