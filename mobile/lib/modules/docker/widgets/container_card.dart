import 'package:flutter/material.dart';
import '../../../data/models/docker_model.dart';

class ContainerCard extends StatelessWidget {
  final DockerContainerModel container;
  final VoidCallback onTap;

  const ContainerCard({
    super.key,
    required this.container,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isRunning = container.isRunning;
    final isStopped = container.isStopped;

    final Color statusColor = isRunning
        ? const Color(0xFF27C93F)
        : (isStopped ? const Color(0xFFFF5F56) : const Color(0xFFFFBD2E));

    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        margin: const EdgeInsets.only(bottom: 10),
        decoration: BoxDecoration(
          color: const Color(0xFF161B22),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isRunning
                ? const Color(0xFF27C93F).withValues(alpha: 0.2)
                : Colors.white10,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Status dot
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: statusColor,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    container.name,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'monospace',
                      color: Colors.white,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                // Short ID badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1117),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: const Color(0xFF30363D)),
                  ),
                  child: Text(
                    container.id.substring(0, container.id.length > 8 ? 8 : container.id.length),
                    style: const TextStyle(
                      fontSize: 10,
                      fontFamily: 'monospace',
                      color: Color(0xFF8B949E),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.layers_outlined, size: 12, color: Color(0xFF8B949E)),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    container.image,
                    style: const TextStyle(
                      fontSize: 11,
                      fontFamily: 'monospace',
                      color: Color(0xFF58A6FF),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.info_outline_rounded, size: 12, color: Color(0xFF8B949E)),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    container.status,
                    style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xFF8B949E),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (container.ports.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFF21262D),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      container.ports.first,
                      style: const TextStyle(
                        fontSize: 10,
                        fontFamily: 'monospace',
                        color: Color(0xFF7EE787),
                      ),
                      maxLines: 1,
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}
