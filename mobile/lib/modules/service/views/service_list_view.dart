import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/service_controller.dart';
import '../widgets/service_card.dart';
import 'service_detail_view.dart';

class ServiceListView extends StatefulWidget {
  const ServiceListView({super.key});

  @override
  State<ServiceListView> createState() => _ServiceListViewState();
}

class _ServiceListViewState extends State<ServiceListView> {
  late final ServiceController controller;

  @override
  void initState() {
    super.initState();
    controller = Get.find<ServiceController>();

    final args = Get.arguments as Map<String, dynamic>? ?? {};
    final workspaceId = args['workspace_id'] as String? ?? Get.parameters['id'] ?? '';
    final serverId = args['server_id'] as String? ?? Get.parameters['serverId'] ?? '';
    final serverName = args['server_name'] as String? ?? 'Server';
    final userRole = args['user_role'] as String? ?? 'VIEWER';

    controller.initContext(
      workspaceId: workspaceId,
      serverId: serverId,
      serverName: serverName,
      userRole: userRole,
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
              const Text(
                'Services (Systemd)',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
              if (controller.currentServerName.value.isNotEmpty)
                Text(
                  controller.currentServerName.value,
                  style: const TextStyle(fontSize: 12, color: Colors.white70),
                ),
            ],
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Services',
            onPressed: () => controller.loadServices(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search & Filter Bar
          Container(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            color: const Color(0xFF1E293B),
            child: Column(
              children: [
                TextField(
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    hintText: 'Cari service (e.g. nginx, odoo, postgres)...',
                    hintStyle: const TextStyle(color: Colors.white38, fontSize: 14),
                    prefixIcon: const Icon(Icons.search, color: Colors.tealAccent, size: 20),
                    filled: true,
                    fillColor: const Color(0xFF0F172A),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide.none,
                    ),
                  ),
                  onChanged: controller.setSearch,
                ),
                const SizedBox(height: 10),
                // Filter chips
                Obx(
                  () => SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _buildFilterChip('all', 'Semua'),
                        const SizedBox(width: 8),
                        _buildFilterChip('active', 'Active (Running)'),
                        const SizedBox(width: 8),
                        _buildFilterChip('inactive', 'Inactive (Stopped)'),
                        const SizedBox(width: 8),
                        _buildFilterChip('failed', 'Failed'),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Content List
          Expanded(
            child: Obx(() {
              if (controller.isLoading.value) {
                return const Center(
                  child: CircularProgressIndicator(color: Colors.tealAccent),
                );
              }

              if (!controller.systemdSupported.value) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.info_outline, size: 56, color: Colors.amberAccent),
                        const SizedBox(height: 16),
                        const Text(
                          'Systemd Tidak Didukung',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          controller.errorMessage.value.isNotEmpty
                              ? controller.errorMessage.value
                              : 'Server target tidak menggunakan systemd sebagai init system atau service management belum didukung.',
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.white70, fontSize: 14),
                        ),
                        const SizedBox(height: 20),
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.teal,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                          onPressed: () => controller.loadServices(),
                          icon: const Icon(Icons.refresh, color: Colors.white),
                          label: const Text(
                            'Coba Periksa Lagi',
                            style: TextStyle(color: Colors.white),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }

              final filtered = controller.filteredServices;

              if (filtered.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.search_off, size: 48, color: Colors.white24),
                      const SizedBox(height: 12),
                      const Text(
                        'Tidak ada service yang cocok',
                        style: TextStyle(color: Colors.white54, fontSize: 15),
                      ),
                      const SizedBox(height: 16),
                      TextButton(
                        onPressed: () {
                          controller.setSearch('');
                          controller.setFilter('all');
                          controller.loadServices();
                        },
                        child: const Text('Reset Filter', style: TextStyle(color: Colors.tealAccent)),
                      ),
                    ],
                  ),
                );
              }

              return RefreshIndicator(
                color: Colors.tealAccent,
                backgroundColor: const Color(0xFF1E293B),
                onRefresh: () => controller.loadServices(silent: true),
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: filtered.length,
                  itemBuilder: (ctx, idx) {
                    final item = filtered[idx];
                    return ServiceCard(
                      service: item,
                      onTap: () {
                        controller.loadServiceDetail(item.name);
                        Get.to(
                          () => ServiceDetailView(serviceName: item.name),
                          transition: Transition.rightToLeft,
                        );
                      },
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

  Widget _buildFilterChip(String value, String label) {
    final isSelected = controller.activeFilter.value == value;
    return InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: () => controller.setFilter(value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? Colors.tealAccent.withValues(alpha: 0.2) : const Color(0xFF0F172A),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? Colors.tealAccent : Colors.white12,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.tealAccent : Colors.white60,
            fontSize: 12,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}
