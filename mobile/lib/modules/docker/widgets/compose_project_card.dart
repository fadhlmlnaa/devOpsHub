import 'package:flutter/material.dart';
import '../../../data/models/docker_model.dart';

class ComposeProjectCard extends StatelessWidget {
  final DockerComposeProjectModel project;
  final DockerComposeStatusModel? status;
  final bool canMutate;
  final VoidCallback onTap;
  final Function(String action) onAction;

  const ComposeProjectCard({
    super.key,
    required this.project,
    this.status,
    required this.canMutate,
    required this.onTap,
    required this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    final statusStr = status?.status ?? 'UNKNOWN';
    Color statusColor = const Color(0xFF8B949E);
    if (statusStr == 'RUNNING') {
      statusColor = const Color(0xFF27C93F);
    } else if (statusStr == 'PARTIAL') {
      statusColor = const Color(0xFFFFBD2E);
    } else if (statusStr == 'STOPPED') {
      statusColor = const Color(0xFFFF5F56);
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: onTap,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFFBC8CFF).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.inventory_2_rounded, size: 20, color: Color(0xFFBC8CFF)),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        project.name,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        'Project: ${project.projectName} | ${project.workingDirectory}',
                        style: const TextStyle(
                          fontSize: 11,
                          fontFamily: 'monospace',
                          color: Color(0xFF8B949E),
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: statusColor.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    statusStr,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'monospace',
                      color: statusColor,
                    ),
                  ),
                ),
              ],
            ),
          ),
          if (status != null && status!.services.isNotEmpty) ...[
            const SizedBox(height: 10),
            const Divider(color: Color(0xFF21262D), height: 1),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: status!.services.map((s) {
                final isSvcRunning = s.isRunning;
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1117),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: isSvcRunning
                          ? const Color(0xFF27C93F).withValues(alpha: 0.3)
                          : const Color(0xFFFF5F56).withValues(alpha: 0.3),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 5,
                        height: 5,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isSvcRunning ? const Color(0xFF27C93F) : const Color(0xFFFF5F56),
                        ),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        s.service ?? s.name,
                        style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: Colors.white70),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 12),
          // Action Buttons
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFF7EE787),
                    side: BorderSide(color: const Color(0xFF7EE787).withValues(alpha: 0.5)),
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                  onPressed: canMutate ? () => onAction('up') : null,
                  icon: const Icon(Icons.play_arrow_rounded, size: 16),
                  label: const Text('UP', style: TextStyle(fontFamily: 'monospace', fontSize: 11, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFFFF7B72),
                    side: BorderSide(color: const Color(0xFFFF7B72).withValues(alpha: 0.5)),
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                  onPressed: canMutate ? () => onAction('down') : null,
                  icon: const Icon(Icons.stop_rounded, size: 16),
                  label: const Text('DOWN', style: TextStyle(fontFamily: 'monospace', fontSize: 11, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFF58A6FF),
                    side: BorderSide(color: const Color(0xFF58A6FF).withValues(alpha: 0.5)),
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                  onPressed: canMutate ? () => onAction('restart') : null,
                  icon: const Icon(Icons.replay_rounded, size: 16),
                  label: const Text('RESTART', style: TextStyle(fontFamily: 'monospace', fontSize: 11, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
