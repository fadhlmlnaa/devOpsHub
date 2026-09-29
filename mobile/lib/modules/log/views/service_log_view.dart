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
  bool _showFilters = true;

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
      backgroundColor: const Color(0xFF090D12), // Deep Terminal Canvas
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18, color: Color(0xFFE6EDF3)),
          onPressed: () => Get.back(),
        ),
        titleSpacing: 0,
        title: Obx(
          () => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.terminal_rounded, size: 16, color: Color(0xFF7EE787)),
                  const SizedBox(width: 6),
                  Text(
                    controller.currentServiceName.value.isNotEmpty
                        ? controller.currentServiceName.value
                        : 'Systemd Logs',
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: Color(0xFFE6EDF3),
                    ),
                  ),
                ],
              ),
              if (controller.currentServerName.value.isNotEmpty)
                Text(
                  'Host: ${controller.currentServerName.value}',
                  style: const TextStyle(fontSize: 10, color: Color(0xFF8B949E), fontFamily: 'monospace'),
                ),
            ],
          ),
        ),
        actions: [
          // Filter toggle button
          IconButton(
            icon: Icon(
              _showFilters ? Icons.tune_rounded : Icons.tune_outlined,
              color: _showFilters ? const Color(0xFF58A6FF) : const Color(0xFF8B949E),
              size: 20,
            ),
            tooltip: 'Filter & Parameter',
            onPressed: () => setState(() => _showFilters = !_showFilters),
          ),
          // Copy all logs
          IconButton(
            icon: const Icon(Icons.copy_all_rounded, color: Color(0xFF8B949E), size: 20),
            tooltip: 'Salin Seluruh Log',
            onPressed: () => controller.copyAllLogs(),
          ),
          // Refresh logs
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF7EE787), size: 20),
            tooltip: 'Refresh Snapshot',
            onPressed: () => controller.loadLogs(),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Collapsible Terminal Filter & Grep Bar
            if (_showFilters) ...[
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
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                color: const Color(0xFF161B22),
                child: Row(
                  children: [
                    Expanded(
                      child: Container(
                        height: 36,
                        decoration: BoxDecoration(
                          color: const Color(0xFF0D1117),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: const Color(0xFF30363D)),
                        ),
                        child: TextField(
                          style: const TextStyle(color: Color(0xFFE6EDF3), fontSize: 12, fontFamily: 'monospace'),
                          decoration: const InputDecoration(
                            hintText: 'grep -i "keyword"...',
                            hintStyle: TextStyle(color: Color(0xFF484F58), fontSize: 12, fontFamily: 'monospace'),
                            prefixIcon: Icon(Icons.search_rounded, color: Color(0xFF58A6FF), size: 16),
                            contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            border: InputBorder.none,
                          ),
                          onChanged: controller.setSearch,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Obx(() {
                      final count = controller.filteredEntries.length;
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFF21262D),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '$count lines',
                          style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF8B949E)),
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ],

            // Terminal Window Title Bar (macOS Style)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: const BoxDecoration(
                color: Color(0xFF161B22),
                border: Border(
                  top: BorderSide(color: Color(0xFF21262D), width: 1),
                  bottom: BorderSide(color: Color(0xFF21262D), width: 1),
                ),
              ),
              child: Row(
                children: [
                  // Traffic light dots
                  Container(width: 10, height: 10, decoration: const BoxDecoration(color: Color(0xFFFF5F56), shape: BoxShape.circle)),
                  const SizedBox(width: 6),
                  Container(width: 10, height: 10, decoration: const BoxDecoration(color: Color(0xFFFFBD2E), shape: BoxShape.circle)),
                  const SizedBox(width: 6),
                  Container(width: 10, height: 10, decoration: const BoxDecoration(color: Color(0xFF27C93F), shape: BoxShape.circle)),
                  const SizedBox(width: 12),
                  Obx(
                    () => Expanded(
                      child: Text(
                        'journalctl -u ${controller.currentServiceName.value} -n ${controller.selectedLines.value}',
                        style: const TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 11,
                          color: Color(0xFF8B949E),
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                  // Terminal View Toggles
                  Obx(
                    () => Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        InkWell(
                          onTap: controller.toggleLineNumbers,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: Text(
                              '#NUM',
                              style: TextStyle(
                                fontSize: 10,
                                fontFamily: 'monospace',
                                fontWeight: FontWeight.bold,
                                color: controller.showLineNumbers.value ? const Color(0xFF58A6FF) : const Color(0xFF484F58),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        InkWell(
                          onTap: controller.toggleTimestamps,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: Text(
                              'TIME',
                              style: TextStyle(
                                fontSize: 10,
                                fontFamily: 'monospace',
                                fontWeight: FontWeight.bold,
                                color: controller.showTimestamps.value ? const Color(0xFF58A6FF) : const Color(0xFF484F58),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Truncation Warning
            Obx(() {
              final res = controller.logResponse.value;
              if (res != null && res.truncated) {
                return Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  color: const Color(0xFFD29922).withValues(alpha: 0.15),
                  child: const Row(
                    children: [
                      Icon(Icons.warning_amber_rounded, size: 14, color: Color(0xFFD29922)),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '[TRUNCATED] Log melebihi batas 1MB, dipotong ke baris terbaru.',
                          style: TextStyle(color: Color(0xFFE3B341), fontSize: 10, fontFamily: 'monospace'),
                        ),
                      ),
                    ],
                  ),
                );
              }
              return const SizedBox.shrink();
            }),

            // Terminal Console Body
            Expanded(
              child: Container(
                color: const Color(0xFF0D1117), // GitHub / VSCode Terminal Black
                child: Obx(() {
                  if (controller.isLoading.value) {
                    return const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(Color(0xFF7EE787))),
                          SizedBox(height: 12),
                          Text(
                            'Executing journalctl over SSH...',
                            style: TextStyle(fontFamily: 'monospace', color: Color(0xFF8B949E), fontSize: 12),
                          ),
                        ],
                      ),
                    );
                  }

                  if (controller.errorMessage.value.isNotEmpty && controller.entries.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.error_outline_rounded, size: 40, color: Color(0xFFFF7B72)),
                            const SizedBox(height: 12),
                            Text(
                              controller.errorMessage.value,
                              textAlign: TextAlign.center,
                              style: const TextStyle(color: Color(0xFFE6EDF3), fontSize: 13, fontFamily: 'monospace'),
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF238636),
                                foregroundColor: Colors.white,
                              ),
                              onPressed: () => controller.loadLogs(),
                              icon: const Icon(Icons.refresh_rounded, size: 16),
                              label: const Text('Coba Lagi', style: TextStyle(fontFamily: 'monospace', fontSize: 12)),
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
                          const Icon(Icons.receipt_long_rounded, size: 40, color: Color(0xFF30363D)),
                          const SizedBox(height: 12),
                          const Text(
                            'Tidak ada baris log ditemukan.',
                            style: TextStyle(color: Color(0xFF8B949E), fontSize: 13, fontFamily: 'monospace'),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Pastikan service pernah berjalan & memiliki entri journald.',
                            style: TextStyle(color: Color(0xFF484F58), fontSize: 11, fontFamily: 'monospace'),
                          ),
                          const SizedBox(height: 16),
                          TextButton.icon(
                            onPressed: () => controller.loadLogs(),
                            icon: const Icon(Icons.refresh_rounded, size: 16, color: Color(0xFF58A6FF)),
                            label: const Text('Muat Ulang', style: TextStyle(color: Color(0xFF58A6FF), fontFamily: 'monospace')),
                          ),
                        ],
                      ),
                    );
                  }

                  return RefreshIndicator(
                    color: const Color(0xFF7EE787),
                    backgroundColor: const Color(0xFF161B22),
                    onRefresh: () => controller.loadLogs(silent: true),
                    child: ListView.builder(
                      controller: controller.scrollController,
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: filtered.length,
                      itemBuilder: (ctx, idx) {
                        final item = filtered[idx];
                        return LogEntryWidget(
                          entry: item,
                          lineNumber: idx + 1,
                          showLineNumber: controller.showLineNumbers.value,
                          showTimestamp: controller.showTimestamps.value,
                          wrap: controller.wrapLines.value,
                          onCopy: () => controller.copyEntry(item.message),
                        );
                      },
                    ),
                  );
                }),
              ),
            ),

            // Terminal Bottom Status Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: const BoxDecoration(
                color: Color(0xFF161B22),
                border: Border(top: BorderSide(color: Color(0xFF21262D), width: 1)),
              ),
              child: Obx(() {
                final count = controller.filteredEntries.length;
                final req = controller.selectedLines.value;
                final since = controller.selectedSince.value ?? 'all';

                return Row(
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Color(0xFF7EE787),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'STATUS: OK | LINES: $count/$req | SINCE: $since',
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 10,
                        color: Color(0xFF8B949E),
                      ),
                    ),
                    const Spacer(),
                    InkWell(
                      onTap: () => controller.scrollToTop(),
                      child: const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 4),
                        child: Text('▲ TOP', style: TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF58A6FF))),
                      ),
                    ),
                    const SizedBox(width: 6),
                    InkWell(
                      onTap: () => controller.scrollToBottom(),
                      child: const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 4),
                        child: Text('▼ BOTTOM', style: TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF58A6FF))),
                      ),
                    ),
                  ],
                );
              }),
            ),
          ],
        ),
      ),
    );
  }
}

