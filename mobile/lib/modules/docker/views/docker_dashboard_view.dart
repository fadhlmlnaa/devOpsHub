import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/widgets/app_bottom_sheet.dart';
import '../controllers/docker_compose_controller.dart';
import '../controllers/docker_controller.dart';
import '../widgets/compose_project_card.dart';
import '../widgets/container_card.dart';
import '../widgets/create_compose_sheet.dart';
import '../widgets/docker_status_card.dart';

class DockerDashboardView extends StatefulWidget {
  final String? workspaceId;
  final String? serverId;
  final String? serverName;
  final String? userRole;

  const DockerDashboardView({
    super.key,
    this.workspaceId,
    this.serverId,
    this.serverName,
    this.userRole,
  });

  @override
  State<DockerDashboardView> createState() => _DockerDashboardViewState();
}

class _DockerDashboardViewState extends State<DockerDashboardView> {
  late final DockerController dockerController;
  late final DockerComposeController composeController;
  int _selectedTab = 0; // 0 = Containers, 1 = Compose Projects

  @override
  void initState() {
    super.initState();
    dockerController = Get.find<DockerController>();
    composeController = Get.find<DockerComposeController>();

    final args = Get.arguments as Map<String, dynamic>? ?? {};
    final wsId = widget.workspaceId ?? args['workspace_id'] as String? ?? Get.parameters['id'] ?? '';
    final srvId = widget.serverId ?? args['server_id'] as String? ?? Get.parameters['serverId'] ?? '';
    final srvName = widget.serverName ?? args['server_name'] as String? ?? 'Server';
    final role = widget.userRole ?? args['role'] as String? ?? 'VIEWER';

    dockerController.initContext(
      workspaceId: wsId,
      serverId: srvId,
      serverName: srvName,
      userRole: role,
    );

    composeController.initContext(
      workspaceId: wsId,
      serverId: srvId,
      userRole: role,
    );
  }

  void _showAddComposeModal(BuildContext context, String wsId, String srvId) {
    AppBottomSheet.show(
      context: context,
      child: CreateComposeSheet(
        workspaceId: wsId,
        serverId: srvId,
      ),
    );
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
        title: Obx(
          () => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.directions_boat_rounded, size: 18, color: Color(0xFF58A6FF)),
                  const SizedBox(width: 8),
                  const Text(
                    'Docker Management',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
                  ),
                ],
              ),
              if (dockerController.currentServerName.value.isNotEmpty)
                Text(
                  'Host: ${dockerController.currentServerName.value}',
                  style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: Color(0xFF8B949E)),
                ),
            ],
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF7EE787)),
            tooltip: 'Refresh Docker',
            onPressed: () {
              dockerController.loadDockerDashboard();
              composeController.loadComposeProjects();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFF58A6FF),
          backgroundColor: const Color(0xFF161B22),
          onRefresh: () async {
            await dockerController.loadDockerDashboard(silent: true);
            await composeController.loadComposeProjects(silent: true);
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Docker Daemon Status Card
                Obx(
                  () => DockerStatusCard(
                    status: dockerController.dockerStatus.value,
                    onRefresh: () => dockerController.loadDockerDashboard(),
                  ),
                ),
                const SizedBox(height: 16),

                // Segmented Tabs: Containers vs Compose Projects
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF161B22),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF30363D)),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: _buildTabButton(
                          0,
                          'Containers',
                          Icons.grid_view_rounded,
                        ),
                      ),
                      Expanded(
                        child: _buildTabButton(
                          1,
                          'Compose Projects',
                          Icons.inventory_2_rounded,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Tab 0: Containers
                if (_selectedTab == 0) _buildContainersTab(context),

                // Tab 1: Compose Projects
                if (_selectedTab == 1) _buildComposeTab(context),
              ],
            ),
          ),
        ),
      ),
      floatingActionButton: _selectedTab == 1 && composeController.canMutate
          ? FloatingActionButton.extended(
              backgroundColor: const Color(0xFF238636),
              icon: const Icon(Icons.add_rounded, color: Colors.white),
              label: const Text('Registrasi Compose', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              onPressed: () => _showAddComposeModal(
                context,
                dockerController.currentWorkspaceId.value,
                dockerController.currentServerId.value,
              ),
            )
          : null,
    );
  }

  Widget _buildTabButton(int index, String title, IconData icon) {
    final isSelected = _selectedTab == index;
    return GestureDetector(
      onTap: () => setState(() => _selectedTab = index),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF21262D) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 16,
              color: isSelected ? const Color(0xFF58A6FF) : const Color(0xFF8B949E),
            ),
            const SizedBox(width: 6),
            Text(
              title,
              style: TextStyle(
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected ? Colors.white : const Color(0xFF8B949E),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContainersTab(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Filter Chips (Running, Stopped, All)
        Row(
          children: [
            _buildFilterChip('running', 'Running'),
            const SizedBox(width: 8),
            _buildFilterChip('stopped', 'Stopped'),
            const SizedBox(width: 8),
            _buildFilterChip('all', 'Semua'),
          ],
        ),
        const SizedBox(height: 12),

        // Search Bar
        Container(
          height: 38,
          decoration: BoxDecoration(
            color: const Color(0xFF161B22),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFF30363D)),
          ),
          child: TextField(
            style: const TextStyle(color: Colors.white, fontSize: 12, fontFamily: 'monospace'),
            decoration: const InputDecoration(
              hintText: 'Cari container (nama, image, ID)...',
              hintStyle: TextStyle(color: Color(0xFF484F58), fontSize: 12),
              prefixIcon: Icon(Icons.search_rounded, color: Color(0xFF58A6FF), size: 16),
              contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 10),
              border: InputBorder.none,
            ),
            onChanged: dockerController.setSearch,
          ),
        ),
        const SizedBox(height: 14),

        // Containers List
        Obx(() {
          if (dockerController.isLoading.value && dockerController.containers.isEmpty) {
            return const Padding(
              padding: EdgeInsets.all(32.0),
              child: Center(
                child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(Color(0xFF58A6FF))),
              ),
            );
          }

          final status = dockerController.dockerStatus.value;
          if (status != null && !status.isRunning) {
            return Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF161B22),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Column(
                children: [
                  Icon(Icons.power_off_rounded, size: 40, color: Color(0xFFFF5F56)),
                  SizedBox(height: 12),
                  Text(
                    'Docker Daemon Tidak Aktif',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Pastikan layanan docker.service berjalan pada host target.',
                    style: TextStyle(color: Color(0xFF8B949E), fontSize: 12),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            );
          }

          final list = dockerController.filteredContainers;
          if (list.isEmpty) {
            return Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: const Color(0xFF161B22),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  const Icon(Icons.inbox_rounded, size: 40, color: Color(0xFF30363D)),
                  const SizedBox(height: 12),
                  const Text('Tidak ada container ditemukan.', style: TextStyle(color: Color(0xFF8B949E), fontSize: 13)),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: () => dockerController.loadContainers(),
                    child: const Text('Muat Ulang', style: TextStyle(color: Color(0xFF58A6FF))),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: list.length,
            itemBuilder: (ctx, idx) {
              final c = list[idx];
              return ContainerCard(
                container: c,
                onTap: () {
                  Get.toNamed(
                    '/workspaces/${dockerController.currentWorkspaceId.value}/servers/${dockerController.currentServerId.value}/docker/containers/${c.id}',
                    arguments: {
                      'workspace_id': dockerController.currentWorkspaceId.value,
                      'server_id': dockerController.currentServerId.value,
                      'server_name': dockerController.currentServerName.value,
                      'container_id': c.id,
                      'container_name': c.name,
                      'role': dockerController.currentUserRole.value,
                    },
                  );
                },
              );
            },
          );
        }),
      ],
    );
  }

  Widget _buildFilterChip(String key, String label) {
    return Obx(() {
      final isSelected = dockerController.selectedStateFilter.value == key;
      return InkWell(
        borderRadius: BorderRadius.circular(6),
        onTap: () => dockerController.setStateFilter(key),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF58A6FF).withValues(alpha: 0.15) : const Color(0xFF161B22),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(
              color: isSelected ? const Color(0xFF58A6FF) : const Color(0xFF30363D),
            ),
          ),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontFamily: 'monospace',
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              color: isSelected ? const Color(0xFF58A6FF) : const Color(0xFF8B949E),
            ),
          ),
        ),
      );
    });
  }

  Widget _buildComposeTab(BuildContext context) {
    return Obx(() {
      if (composeController.isLoading.value && composeController.projects.isEmpty) {
        return const Padding(
          padding: EdgeInsets.all(32.0),
          child: Center(
            child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(Color(0xFFBC8CFF))),
          ),
        );
      }

      final list = composeController.projects;
      if (list.isEmpty) {
        return Container(
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: const Color(0xFF161B22),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              const Icon(Icons.inventory_2_outlined, size: 40, color: Color(0xFF30363D)),
              const SizedBox(height: 12),
              const Text('Belum ada Docker Compose project terdaftar.', style: TextStyle(color: Color(0xFF8B949E), fontSize: 13)),
              const SizedBox(height: 4),
              const Text(
                'Daftarkan compose file yang ada pada host server untuk manajemen cluster.',
                style: TextStyle(color: Color(0xFF484F58), fontSize: 11),
                textAlign: TextAlign.center,
              ),
              if (composeController.canMutate) ...[
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF238636)),
                  onPressed: () => _showAddComposeModal(
                    context,
                    dockerController.currentWorkspaceId.value,
                    dockerController.currentServerId.value,
                  ),
                  icon: const Icon(Icons.add_rounded, color: Colors.white, size: 16),
                  label: const Text('Registrasi Compose', style: TextStyle(color: Colors.white)),
                ),
              ],
            ],
          ),
        );
      }

      return ListView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: list.length,
        itemBuilder: (ctx, idx) {
          final p = list[idx];
          final status = composeController.projectStatuses[p.id];
          return ComposeProjectCard(
            project: p,
            status: status,
            canMutate: composeController.canMutate,
            onTap: () {
              // Navigate to detail
            },
            onAction: (action) {
              composeController.showComposeActionDialog(
                context: context,
                projectId: p.id,
                projectName: p.projectName,
                action: action,
              );
            },
          );
        },
      );
    });
  }
}
