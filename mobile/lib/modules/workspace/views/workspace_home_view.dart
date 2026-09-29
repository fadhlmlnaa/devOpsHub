import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_bottom_sheet.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_status_badge.dart';
import '../../auth/controllers/auth_controller.dart';
import '../../environment/controllers/environment_controller.dart';
import '../../environment/widgets/create_environment_sheet.dart';
import '../../server/controllers/server_controller.dart';
import '../../alerts/controllers/notification_controller.dart';
import '../controllers/workspace_controller.dart';

class WorkspaceHomeView extends StatefulWidget {
  const WorkspaceHomeView({super.key});

  @override
  State<WorkspaceHomeView> createState() => _WorkspaceHomeViewState();
}

class _WorkspaceHomeViewState extends State<WorkspaceHomeView> {
  final WorkspaceController _workspaceController = Get.find<WorkspaceController>();
  final EnvironmentController _envController = Get.find<EnvironmentController>();
  final ServerController _serverController = Get.find<ServerController>();
  final AuthController _authController = Get.find<AuthController>();

  int _selectedTab = 0; // 0 = Environments, 1 = Servers

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  void _loadData() {
    final ws = _workspaceController.selectedWorkspace.value;
    if (ws != null) {
      _envController.loadEnvironments(ws.id);
      _serverController.loadServers(ws.id);
    }
  }

  void _showAddEnvironmentModal(BuildContext context, String wsId) {
    AppBottomSheet.show(
      context: context,
      child: CreateEnvironmentSheet(workspaceId: wsId),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppAppBar(
        title: 'Workspace Home',
        actions: [
          // Audit Logs shortcut (OWNER / ADMIN)
          Obx(() {
            final ws = _workspaceController.selectedWorkspace.value;
            final isOwnerOrAdmin = ws?.role == 'OWNER' || ws?.role == 'ADMIN';
            if (!isOwnerOrAdmin) return const SizedBox.shrink();
            return IconButton(
              tooltip: 'Audit Logs',
              icon: const Icon(Icons.security_outlined, color: AppColors.primary, size: 22),
              onPressed: () {
                if (ws != null) {
                  Get.toNamed('/workspaces/${ws.id}/audit-logs', parameters: {'id': ws.id});
                }
              },
            );
          }),
          // Alerts Dashboard shortcut
          IconButton(
            tooltip: 'Peringatan & Alert',
            icon: const Icon(Icons.notifications_active_outlined, color: AppColors.primary, size: 22),
            onPressed: () {
              final ws = _workspaceController.selectedWorkspace.value;
              if (ws != null) {
                Get.toNamed('/workspaces/${ws.id}/alerts', parameters: {'id': ws.id});
              }
            },
          ),
          // Notification Inbox with dynamic Badge
          Builder(
            builder: (context) {
              final notifCtrl = Get.find<NotificationController>();
              final ws = _workspaceController.selectedWorkspace.value;
              if (ws != null) {
                notifCtrl.initWorkspace(ws.id);
              }
              return Obx(() {
                final unread = notifCtrl.unreadCount.value;
                return Stack(
                  alignment: Alignment.center,
                  children: [
                    IconButton(
                      tooltip: 'Inbox Notifikasi',
                      icon: const Icon(Icons.notifications_outlined, color: AppColors.textPrimary, size: 22),
                      onPressed: () {
                        if (ws != null) {
                          Get.toNamed('/workspaces/${ws.id}/notifications', parameters: {'id': ws.id});
                        }
                      },
                    ),
                    if (unread > 0)
                      Positioned(
                        top: 8,
                        right: 8,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: const BoxDecoration(
                            color: AppColors.error,
                            shape: BoxShape.circle,
                          ),
                          constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                          child: Text(
                            unread > 99 ? '99+' : '$unread',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ),
                  ],
                );
              });
            },
          ),
          IconButton(
            tooltip: 'Ganti Workspace',
            icon: const Icon(Icons.swap_horiz_rounded, color: AppColors.textSecondary),
            onPressed: () => Get.back(),
          ),
          IconButton(
            tooltip: 'Logout',
            icon: const Icon(Icons.logout_rounded, color: AppColors.textSecondary, size: 20),
            onPressed: () {
              Get.defaultDialog(
                title: 'Konfirmasi Logout',
                titleStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                middleText: 'Apakah Anda yakin ingin keluar dari sesi ini?',
                backgroundColor: AppColors.surface,
                textConfirm: 'Logout',
                textCancel: 'Batal',
                confirmTextColor: Colors.white,
                buttonColor: AppColors.error,
                cancelTextColor: AppColors.textSecondary,
                onConfirm: () {
                  Get.back();
                  _authController.logout();
                },
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Obx(() {
          final workspace = _workspaceController.selectedWorkspace.value;
          if (workspace == null) {
            return Center(
              child: ElevatedButton(
                onPressed: () => Get.offNamed('/workspaces'),
                child: const Text('Pilih Workspace'),
              ),
            );
          }

          final isOwnerOrAdmin = workspace.role.toUpperCase() == 'OWNER' || workspace.role.toUpperCase() == 'ADMIN';

          return RefreshIndicator(
            color: AppColors.primary,
            backgroundColor: AppColors.surfaceElevated,
            onRefresh: () async => _loadData(),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Workspace Header Card
                  AppCard(
                    gradient: AppColors.surfaceGradient,
                    borderColor: AppColors.borderFocused.withValues(alpha: 0.3),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: const Icon(Icons.apartment_rounded, color: AppColors.primary, size: 26),
                            ),
                            AppStatusBadge.role(workspace.role),
                          ],
                        ),
                        const SizedBox(height: 14),
                        Text(
                          workspace.name,
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
                        ),
                        if (workspace.description != null && workspace.description!.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            workspace.description!,
                            style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                          ),
                        ],
                        const SizedBox(height: 12),
                        const Divider(color: AppColors.border, height: 1),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            const Icon(Icons.schedule_rounded, size: 14, color: AppColors.textMuted),
                            const SizedBox(width: 6),
                            Text(
                              workspace.timezone,
                              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                            ),
                            const Spacer(),
                            Flexible(
                              child: Text(
                                'ID: #${workspace.id.length > 8 ? workspace.id.substring(0, 8) : workspace.id}',
                                style: const TextStyle(fontSize: 11, color: AppColors.textMuted, fontFamily: 'monospace'),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Segmented Tabs: Environments vs Servers
                  Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceElevated,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Row(
                      children: [
                        Expanded(child: _buildTabButton(0, 'Environments (${_envController.environments.length})', Icons.layers_rounded)),
                        Expanded(child: _buildTabButton(1, 'Servers (${_serverController.servers.length})', Icons.dns_rounded)),
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Tab 0: Environments List
                  if (_selectedTab == 0) ...[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Daftar Environment',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                        ),
                        if (isOwnerOrAdmin)
                          TextButton.icon(
                            icon: const Icon(Icons.add_rounded, size: 18),
                            label: const Text('Tambah'),
                            onPressed: () => _showAddEnvironmentModal(context, workspace.id),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    _buildEnvironmentList(workspace.id, isOwnerOrAdmin),
                  ],

                  // Tab 1: Servers List
                  if (_selectedTab == 1) ...[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Daftar Server',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                        ),
                        if (isOwnerOrAdmin)
                          TextButton.icon(
                            icon: const Icon(Icons.add_rounded, size: 18),
                            label: const Text('Tambah'),
                            onPressed: () => Get.toNamed('/workspaces/${workspace.id}/servers/add'),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    _buildServerList(workspace.id),
                  ],

                  const SizedBox(height: 24),
                  const Divider(color: AppColors.border, height: 1),
                  const SizedBox(height: 20),

                  // DevOps Roadmap & Modules Section
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'DevOps Modules & Capabilities',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppColors.success.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: AppColors.success.withValues(alpha: 0.3)),
                        ),
                        child: const Text('All 16 Modules Ready', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.success)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(child: _buildRoadmapCard(icon: Icons.speed_rounded, title: 'Monitoring', step: 'Telemetry', isActive: true)),
                      const SizedBox(width: 10),
                      Expanded(child: _buildRoadmapCard(icon: Icons.miscellaneous_services_rounded, title: 'Services', step: 'Systemd', isActive: true)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(child: _buildRoadmapCard(icon: Icons.terminal_rounded, title: 'Logs & Journal', step: 'Audit/Stream', isActive: true)),
                      const SizedBox(width: 10),
                      Expanded(child: _buildRoadmapCard(icon: Icons.directions_boat_rounded, title: 'Docker Engine', step: 'Containers', isActive: true)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(child: _buildRoadmapCard(icon: Icons.rocket_launch_rounded, title: 'Deployments', step: 'Pipelines', isActive: true)),
                      const SizedBox(width: 10),
                      Expanded(child: _buildRoadmapCard(icon: Icons.backup_rounded, title: 'Database Backup', step: 'Snapshots', isActive: true)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(child: _buildRoadmapCard(icon: Icons.notifications_active_rounded, title: 'Alert Engine', step: 'Real-Time', isActive: true)),
                      const SizedBox(width: 10),
                      Expanded(child: _buildRoadmapCard(icon: Icons.hub_rounded, title: 'DevOps Agent', step: 'Outbound WSS', isActive: true)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(child: _buildRoadmapCard(icon: Icons.security_rounded, title: 'Security & RBAC', step: 'Audit Trail', isActive: true)),
                      const SizedBox(width: 10),
                      Expanded(child: _buildRoadmapCard(icon: Icons.verified_user_rounded, title: 'Production Ready', step: 'Hardened', isActive: true)),
                    ],
                  ),

                ],
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildTabButton(int index, String title, IconData icon) {
    final isSelected = _selectedTab == index;
    return GestureDetector(
      onTap: () => setState(() => _selectedTab = index),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(9),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 16,
              color: isSelected ? AppColors.textOnPrimary : AppColors.textSecondary,
            ),
            const SizedBox(width: 6),
            Text(
              title,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: isSelected ? AppColors.textOnPrimary : AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEnvironmentList(String workspaceId, bool isOwnerOrAdmin) {
    final envs = _envController.environments;

    if (_envController.isLoading.value && envs.isEmpty) {
      return const Padding(
        padding: EdgeInsets.all(24.0),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(AppColors.primary))),
      );
    }

    if (envs.isEmpty) {
      return AppCard(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20.0),
          child: Column(
            children: [
              const Icon(Icons.layers_clear_rounded, size: 36, color: AppColors.textMuted),
              const SizedBox(height: 8),
              const Text('Belum ada Environment', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              const SizedBox(height: 4),
              const Text('Tambahkan environment seperti Production, Staging, atau Dev.', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
              if (isOwnerOrAdmin) ...[
                const SizedBox(height: 14),
                AppButton(
                  text: 'Tambah Environment',
                  width: 180,
                  height: 38,
                  onPressed: () => _showAddEnvironmentModal(context, workspaceId),
                ),
              ],
            ],
          ),
        ),
      );
    }

    return Column(
      children: envs.map((env) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 10.0),
          child: AppCard(
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: const Icon(Icons.layers_rounded, color: AppColors.primary, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(env.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.surface,
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(color: AppColors.border),
                            ),
                            child: Text(env.key, style: const TextStyle(fontSize: 10, color: AppColors.textSecondary, fontFamily: 'monospace')),
                          ),
                        ],
                      ),
                      if (env.description != null) ...[
                        const SizedBox(height: 2),
                        Text(env.description!, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      ],
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text('${env.serverCount} Server', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.primary)),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildServerList(String workspaceId) {
    final servers = _serverController.servers;

    if (_serverController.isLoading.value && servers.isEmpty) {
      return const Padding(
        padding: EdgeInsets.all(24.0),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(AppColors.primary))),
      );
    }

    if (servers.isEmpty) {
      return AppCard(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20.0),
          child: Column(
            children: [
              const Icon(Icons.dns_rounded, size: 36, color: AppColors.textMuted),
              const SizedBox(height: 8),
              const Text('Belum ada Server', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              const SizedBox(height: 4),
              const Text('Hubungkan server Linux Anda menggunakan kredensial SSH.', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
              const SizedBox(height: 14),
              AppButton(
                text: 'Tambah Server',
                width: 160,
                height: 38,
                onPressed: () => Get.toNamed('/workspaces/$workspaceId/servers/add'),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      children: servers.map((srv) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 10.0),
          child: AppCard(
            onTap: () {
              _serverController.selectedServer.value = srv;
              Get.toNamed(
                '/workspaces/$workspaceId/servers/${srv.id}',
                arguments: {
                  'workspaceId': workspaceId,
                  'serverId': srv.id,
                  'server': srv,
                },
              );
            },
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: const Icon(Icons.dns_rounded, color: AppColors.primary, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(srv.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14), maxLines: 1, overflow: TextOverflow.ellipsis),
                          ),
                          const SizedBox(width: 6),
                          _buildMiniStatusBadge(srv.status),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Text(srv.ipAddress ?? srv.hostname ?? '-', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, fontFamily: 'monospace')),
                          const SizedBox(width: 8),
                          if (srv.environment != null)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                              decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(4)),
                              child: Text(srv.environment!.name, style: const TextStyle(fontSize: 10, color: AppColors.textMuted)),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded, color: AppColors.textMuted, size: 20),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildMiniStatusBadge(String status) {
    Color color;
    switch (status.toUpperCase()) {
      case 'ONLINE':
        color = AppColors.success;
        break;
      case 'OFFLINE':
        color = AppColors.error;
        break;
      default:
        color = AppColors.textMuted;
    }
    return Container(
      width: 8,
      height: 8,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color),
    );
  }

  Widget _buildRoadmapCard({
    required IconData icon,
    required String title,
    required String step,
    bool isActive = false,
  }) {
    return AppCard(
      padding: const EdgeInsets.all(12),
      borderColor: isActive ? AppColors.primary.withValues(alpha: 0.3) : AppColors.border,
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: isActive ? AppColors.primary.withValues(alpha: 0.12) : AppColors.surfaceElevated,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Icon(icon, size: 16, color: isActive ? AppColors.primary : AppColors.textMuted),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: isActive ? AppColors.textPrimary : AppColors.textSecondary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (isActive)
                      Container(
                        width: 6,
                        height: 6,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: AppColors.success,
                        ),
                      ),
                  ],
                ),
                Text(
                  isActive ? '$step (Ready)' : '$step (Upcoming)',
                  style: TextStyle(
                    fontSize: 10,
                    color: isActive ? AppColors.primary : AppColors.textMuted,
                    fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
