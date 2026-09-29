import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../controllers/docker_controller.dart';
import 'container_log_view.dart';

class ContainerDetailView extends StatefulWidget {
  final String? workspaceId;
  final String? serverId;
  final String? serverName;
  final String? containerId;
  final String? containerName;
  final String? userRole;

  const ContainerDetailView({
    super.key,
    this.workspaceId,
    this.serverId,
    this.serverName,
    this.containerId,
    this.containerName,
    this.userRole,
  });

  @override
  State<ContainerDetailView> createState() => _ContainerDetailViewState();
}

class _ContainerDetailViewState extends State<ContainerDetailView> {
  late final DockerController controller;
  late final String cId;
  late final String wsId;
  late final String srvId;
  late final String srvName;
  late final String role;

  @override
  void initState() {
    super.initState();
    controller = Get.find<DockerController>();

    final args = Get.arguments as Map<String, dynamic>? ?? {};
    wsId = widget.workspaceId ?? args['workspace_id'] as String? ?? Get.parameters['id'] ?? '';
    srvId = widget.serverId ?? args['server_id'] as String? ?? Get.parameters['serverId'] ?? '';
    srvName = widget.serverName ?? args['server_name'] as String? ?? 'Server';
    cId = widget.containerId ?? args['container_id'] as String? ?? Get.parameters['containerId'] ?? '';
    role = widget.userRole ?? args['role'] as String? ?? 'VIEWER';

    controller.initContext(
      workspaceId: wsId,
      serverId: srvId,
      serverName: srvName,
      userRole: role,
    );

    controller.loadContainerDetail(cId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF090D12),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18, color: Color(0xFFE6EDF3)),
          onPressed: () => Get.back(),
        ),
        title: Text(
          cId,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white, fontFamily: 'monospace'),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF7EE787)),
            onPressed: () => controller.loadContainerDetail(cId),
          ),
        ],
      ),
      body: SafeArea(
        child: Obx(() {
          if (controller.isLoading.value && controller.containerDetail.value == null) {
            return const Center(
              child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(Color(0xFF58A6FF))),
            );
          }

          final detail = controller.containerDetail.value;
          if (detail == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline_rounded, size: 48, color: Color(0xFFFF7B72)),
                  const SizedBox(height: 12),
                  const Text('Container tidak ditemukan.', style: TextStyle(color: Colors.white70, fontSize: 14)),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => controller.loadContainerDetail(cId),
                    child: const Text('Coba Lagi'),
                  ),
                ],
              ),
            );
          }

          final isRunning = detail.isRunning;
          final statusColor = isRunning ? const Color(0xFF27C93F) : const Color(0xFFFF5F56);

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF161B22),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: isRunning ? const Color(0xFF27C93F).withValues(alpha: 0.3) : Colors.white10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              detail.name,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                fontFamily: 'monospace',
                                color: Colors.white,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: statusColor.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: statusColor.withValues(alpha: 0.4)),
                            ),
                            child: Text(
                              detail.state.toUpperCase(),
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                fontFamily: 'monospace',
                                color: statusColor,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Image: ${detail.image}',
                        style: const TextStyle(fontSize: 12, fontFamily: 'monospace', color: Color(0xFF58A6FF)),
                      ),
                      Text(
                        'Status: ${detail.status}',
                        style: const TextStyle(fontSize: 11, color: Color(0xFF8B949E)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Specifications Card
                AppCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Informasi Container',
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white70),
                      ),
                      const SizedBox(height: 12),
                      const Divider(color: Color(0xFF21262D), height: 1),
                      const SizedBox(height: 12),
                      _buildSpecRow('Container ID', detail.id),
                      _buildSpecRow('Restart Policy', detail.restartPolicy ?? 'no'),
                      if (detail.ports.isNotEmpty) _buildSpecRow('Port Bindings', detail.ports.join(', ')),
                      if (detail.createdAt != null) _buildSpecRow('Dibuat Pada', detail.createdAt!.length > 19 ? detail.createdAt!.substring(0, 19) : detail.createdAt!),
                      if (detail.startedAt != null) _buildSpecRow('Dimulai Pada', detail.startedAt!.length > 19 ? detail.startedAt!.substring(0, 19) : detail.startedAt!),
                      if (detail.cpuUsage != null) _buildSpecRow('CPU Usage', detail.cpuUsage!),
                      if (detail.memoryUsage != null) _buildSpecRow('Memory Usage', detail.memoryUsage!),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Actions Card
                AppCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Kontrol Container',
                            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white70),
                          ),
                          if (!controller.canMutate)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.orange.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text('Read Only', style: TextStyle(fontSize: 10, color: Colors.orange)),
                            ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: const Color(0xFF7EE787),
                                side: BorderSide(color: const Color(0xFF7EE787).withValues(alpha: 0.5)),
                                padding: const EdgeInsets.symmetric(vertical: 12),
                              ),
                              onPressed: controller.canMutate && !isRunning
                                  ? () => controller.showActionConfirmationDialog(
                                        context: context,
                                        containerId: detail.id,
                                        containerName: detail.name,
                                        action: 'start',
                                      )
                                  : null,
                              icon: const Icon(Icons.play_arrow_rounded, size: 18),
                              label: const Text('START', style: TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold)),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: const Color(0xFFFF7B72),
                                side: BorderSide(color: const Color(0xFFFF7B72).withValues(alpha: 0.5)),
                                padding: const EdgeInsets.symmetric(vertical: 12),
                              ),
                              onPressed: controller.canMutate && isRunning
                                  ? () => controller.showActionConfirmationDialog(
                                        context: context,
                                        containerId: detail.id,
                                        containerName: detail.name,
                                        action: 'stop',
                                      )
                                  : null,
                              icon: const Icon(Icons.stop_rounded, size: 18),
                              label: const Text('STOP', style: TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold)),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: const Color(0xFF58A6FF),
                                side: BorderSide(color: const Color(0xFF58A6FF).withValues(alpha: 0.5)),
                                padding: const EdgeInsets.symmetric(vertical: 12),
                              ),
                              onPressed: controller.canMutate
                                  ? () => controller.showActionConfirmationDialog(
                                        context: context,
                                        containerId: detail.id,
                                        containerName: detail.name,
                                        action: 'restart',
                                      )
                                  : null,
                              icon: const Icon(Icons.replay_rounded, size: 18),
                              label: const Text('RESTART', style: TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold)),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      // View Container Logs
                      AppButton(
                        text: 'Lihat Log Container (stdout/stderr)',
                        icon: const Icon(Icons.terminal_rounded),
                        onPressed: () {
                          Get.to(
                            () => ContainerLogView(
                              workspaceId: wsId,
                              serverId: srvId,
                              serverName: srvName,
                              containerId: detail.id,
                              containerName: detail.name,
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }),
      ),
    );
  }

  Widget _buildSpecRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFF8B949E))),
          ),
          Expanded(
            child: SelectableText(
              value,
              style: const TextStyle(fontSize: 12, fontFamily: 'monospace', color: Colors.white, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
