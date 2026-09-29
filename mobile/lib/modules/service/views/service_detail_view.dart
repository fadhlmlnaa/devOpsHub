import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/service_controller.dart';
import '../widgets/service_action_button.dart';

class ServiceDetailView extends StatelessWidget {
  final String serviceName;

  const ServiceDetailView({
    super.key,
    required this.serviceName,
  });

  Color _getStatusColor(String status) {
    switch (status) {
      case 'RUNNING':
        return Colors.greenAccent;
      case 'STOPPED':
        return Colors.blueGrey;
      case 'FAILED':
        return Colors.redAccent;
      default:
        return Colors.amber;
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<ServiceController>();

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: Text(
          serviceName,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Status',
            onPressed: () => controller.loadServiceDetail(serviceName),
          ),
        ],
      ),
      body: Obx(() {
        final service = controller.selectedService.value;
        final isActionLoading = controller.isActionLoading.value;
        final canMutate = controller.canMutate;

        if (controller.isLoading.value && service == null) {
          return const Center(
            child: CircularProgressIndicator(color: Colors.tealAccent),
          );
        }

        if (service == null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
                const SizedBox(height: 12),
                const Text(
                  'Gagal memuat detail service.',
                  style: TextStyle(color: Colors.white70, fontSize: 16),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.teal),
                  onPressed: () => controller.loadServiceDetail(serviceName),
                  child: const Text('Coba Lagi', style: TextStyle(color: Colors.white)),
                ),
              ],
            ),
          );
        }

        final statusColor = _getStatusColor(service.status);

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: service.isFailed
                        ? Colors.redAccent.withValues(alpha: 0.4)
                        : Colors.tealAccent.withValues(alpha: 0.2),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Icon(
                            Icons.settings_applications,
                            color: statusColor,
                            size: 28,
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                service.name,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: statusColor.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(color: statusColor.withValues(alpha: 0.5)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Container(
                                      width: 6,
                                      height: 6,
                                      decoration: BoxDecoration(
                                        color: statusColor,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      service.status,
                                      style: TextStyle(
                                        color: statusColor,
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    if (service.description != null && service.description!.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      const Divider(color: Colors.white10),
                      const SizedBox(height: 8),
                      Text(
                        service.description!,
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 14,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Action Buttons Section
              const Text(
                'Service Actions',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 6),

              if (!canMutate)
                Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.orange.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.orange.withValues(alpha: 0.3)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.lock_outline, color: Colors.orangeAccent, size: 18),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Aksi service hanya dapat dijalankan oleh OWNER atau ADMIN workspace.',
                          style: TextStyle(color: Colors.orangeAccent, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),

              GridView.count(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 2.4,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  ServiceActionButton(
                    label: 'Start',
                    icon: Icons.play_arrow,
                    color: Colors.greenAccent,
                    isEnabled: canMutate && !service.isRunning && !isActionLoading,
                    isLoading: isActionLoading && controller.actionType.value == 'start',
                    onPressed: () => controller.confirmAndExecuteAction(
                      context: context,
                      serviceName: service.name,
                      action: 'start',
                    ),
                  ),
                  ServiceActionButton(
                    label: 'Stop',
                    icon: Icons.stop,
                    color: Colors.redAccent,
                    isEnabled: canMutate && service.isRunning && !isActionLoading,
                    isLoading: isActionLoading && controller.actionType.value == 'stop',
                    onPressed: () => controller.confirmAndExecuteAction(
                      context: context,
                      serviceName: service.name,
                      action: 'stop',
                    ),
                  ),
                  ServiceActionButton(
                    label: 'Restart',
                    icon: Icons.replay,
                    color: Colors.orangeAccent,
                    isEnabled: canMutate && !isActionLoading,
                    isLoading: isActionLoading && controller.actionType.value == 'restart',
                    onPressed: () => controller.confirmAndExecuteAction(
                      context: context,
                      serviceName: service.name,
                      action: 'restart',
                    ),
                  ),
                  ServiceActionButton(
                    label: 'Reload',
                    icon: Icons.refresh,
                    color: Colors.tealAccent,
                    isEnabled: canMutate && service.isRunning && !isActionLoading,
                    isLoading: isActionLoading && controller.actionType.value == 'reload',
                    onPressed: () => controller.confirmAndExecuteAction(
                      context: context,
                      serviceName: service.name,
                      action: 'reload',
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              // System Specifications Card
              const Text(
                'Spesifikasi Unit Systemd',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),

              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                ),
                child: Column(
                  children: [
                    _buildDetailRow('Load State', service.loadState),
                    const Divider(color: Colors.white10),
                    _buildDetailRow('Active State', service.activeState),
                    const Divider(color: Colors.white10),
                    _buildDetailRow('Sub State', service.subState),
                    const Divider(color: Colors.white10),
                    _buildDetailRow(
                      'Startup Boot (Enabled)',
                      service.enabled == true
                          ? 'Ya (Enabled)'
                          : (service.enabled == false ? 'Tidak (Disabled)' : 'N/A'),
                    ),
                    const Divider(color: Colors.white10),
                    _buildDetailRow(
                      'Main PID',
                      service.mainPid != null ? '${service.mainPid}' : 'N/A (Tidak aktif)',
                    ),
                    if (service.activeEnterTimestamp != null) ...[
                      const Divider(color: Colors.white10),
                      _buildDetailRow('Waktu Aktif', service.activeEnterTimestamp!),
                    ],
                  ],
                ),
              ),

              const SizedBox(height: 32),
            ],
          ),
        );
      }),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: const TextStyle(color: Colors.white54, fontSize: 13),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ),
    );
  }
}
