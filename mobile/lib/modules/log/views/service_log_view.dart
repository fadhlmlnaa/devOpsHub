import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/log_controller.dart';
import '../widgets/log_entry_widget.dart';
import '../widgets/log_filter_widget.dart';

class ServiceLogView extends StatefulWidget {
  final String? workspaceId;
  final String? serverId;
  final String? serverName;
  final String? serviceName;

  const ServiceLogView({
    super.key,
    this.workspaceId,
    this.serverId,
    this.serverName,
    this.serviceName,
  });

  @override
  State<ServiceLogView> createState() => _ServiceLogViewState();
}

class _ServiceLogViewState extends State<ServiceLogView> {
  late final LogController controller;

  @override
  void initState() {
    super.initState();
    controller = Get.find<LogController>();

    final args = Get.arguments as Map<String, dynamic>? ?? {};
    final wsId = widget.workspaceId ?? args['workspace_id'] as String? ?? Get.parameters['id'] ?? '';
    final srvId = widget.serverId ?? args['server_id'] as String? ?? Get.parameters['serverId'] ?? '';
    final srvName = widget.serverName ?? args['server_name'] as String? ?? 'Server';
    final svcName = widget.serviceName ?? args['service_name'] as String? ?? Get.parameters['serviceName'] ?? '';

    controller.initContext(
      workspaceId: wsId,
      serverId: srvId,
      serviceName: svcName,
      serverName: srvName,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: Obx(
          () => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Logs: ${controller.currentServiceName.value}',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              if (controller.currentServerName.value.isNotEmpty)
                Text(
                  controller.currentServerName.value,
                  style: const TextStyle(fontSize: 11, color: Colors.white60),
                ),
            ],
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.copy_all_rounded),
            tooltip: 'Salin Seluruh Log',
            onPressed: () => controller.copyAllLogs(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Log',
            onPressed: () => controller.loadLogs(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter Bar
          Obx(
            () => LogFilterWidget(
              selectedLines: controller.selectedLines.value,
              selectedSince: controller.selectedSince.value,
              onLinesChanged: controller.setLines,
              onSinceChanged: controller.setSince,
            ),
          ),

          // Search Field
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: const Color(0xFF1E293B),
            child: TextField(
              style: const TextStyle(color: Colors.white, fontSize: 13),
              decoration: InputDecoration(
                hintText: 'Cari dalam log...',
                hintStyle: const TextStyle(color: Colors.white38, fontSize: 13),
                prefixIcon: const Icon(Icons.search, color: Colors.tealAccent, size: 18),
                filled: true,
                fillColor: const Color(0xFF0F172A),
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: BorderSide.none,
                ),
              ),
              onChanged: controller.setSearch,
            ),
          ),

          // Truncated Warning Banner
          Obx(() {
            final res = controller.logResponse.value;
            if (res != null && res.truncated) {
              return Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                color: Colors.amber.withValues(alpha: 0.15),
                child: const Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, size: 16, color: Colors.amberAccent),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Ukuran log melebihi batas maksimal 1MB dan dipotong sebagian.',
                        style: TextStyle(color: Colors.amberAccent, fontSize: 11),
                      ),
                    ),
                  ],
                ),
              );
            }
            return const SizedBox.shrink();
          }),

          // Content List
          Expanded(
            child: Obx(() {
              if (controller.isLoading.value) {
                return const Center(
                  child: CircularProgressIndicator(color: Colors.tealAccent),
                );
              }

              if (controller.errorMessage.value.isNotEmpty && controller.entries.isEmpty) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
                        const SizedBox(height: 12),
                        Text(
                          controller.errorMessage.value,
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.white70, fontSize: 14),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.teal),
                          onPressed: () => controller.loadLogs(),
                          icon: const Icon(Icons.refresh, color: Colors.white),
                          label: const Text('Coba Lagi', style: TextStyle(color: Colors.white)),
                        ),
                      ],
                    ),
                  ),
                );
              }

              final filtered = controller.filteredEntries;

              if (filtered.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.receipt_long_outlined, size: 48, color: Colors.white24),
                      const SizedBox(height: 12),
                      const Text(
                        'Tidak ada baris log ditemukan.',
                        style: TextStyle(color: Colors.white54, fontSize: 14),
                      ),
                      const SizedBox(height: 16),
                      TextButton(
                        onPressed: () => controller.loadLogs(),
                        child: const Text('Muat Ulang', style: TextStyle(color: Colors.tealAccent)),
                      ),
                    ],
                  ),
                );
              }

              return RefreshIndicator(
                color: Colors.tealAccent,
                backgroundColor: const Color(0xFF1E293B),
                onRefresh: () => controller.loadLogs(silent: true),
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: filtered.length,
                  itemBuilder: (ctx, idx) {
                    final item = filtered[idx];
                    return LogEntryWidget(
                      entry: item,
                      onCopy: () => controller.copyEntry(item.message),
                    );
                  },
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}
