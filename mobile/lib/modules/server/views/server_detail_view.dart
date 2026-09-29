import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_status_badge.dart';
import '../../../data/models/monitoring_metrics_model.dart';
import '../../../data/models/server_model.dart';
import '../controllers/server_controller.dart';

class ServerDetailView extends StatefulWidget {
  const ServerDetailView({super.key});

  @override
  State<ServerDetailView> createState() => _ServerDetailViewState();
}

class _ServerDetailViewState extends State<ServerDetailView> {
  final ServerController _controller = Get.find<ServerController>();
  late final String _workspaceId;
  late final String _serverId;

  @override
  void initState() {
    super.initState();
    final args = Get.arguments is Map ? Get.arguments as Map : {};
    _workspaceId = (args['workspaceId'] as String?)?.isNotEmpty == true
        ? args['workspaceId'] as String
        : (Get.parameters['id'] ?? '');
    _serverId = (args['serverId'] as String?)?.isNotEmpty == true
        ? args['serverId'] as String
        : (Get.parameters['serverId'] ?? '');

    if (args['server'] is ServerModel) {
      _controller.selectedServer.value = args['server'] as ServerModel;
    }

    if (_workspaceId.isNotEmpty && _serverId.isNotEmpty) {
      _controller.loadServerDetail(_workspaceId, _serverId);
      _controller.loadServerMetrics(_workspaceId, _serverId);
    }
  }

  Future<void> _onRefresh() async {
    if (_workspaceId.isNotEmpty && _serverId.isNotEmpty) {
      await Future.wait([
        _controller.loadServerDetail(_workspaceId, _serverId),
        _controller.loadServerMetrics(_workspaceId, _serverId, silent: true),
      ]);
    }
  }

  void _onTestConnection() {
    if (_workspaceId.isNotEmpty && _serverId.isNotEmpty) {
      _controller.testConnection(_workspaceId, _serverId);
    }
  }

  void _onDeleteServer() {
    Get.defaultDialog(
      title: 'Hapus Server',
      titleStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
      middleText: 'Apakah Anda yakin ingin menghapus server ini beserta seluruh kredensialnya?',
      backgroundColor: AppColors.surface,
      textConfirm: 'Hapus',
      textCancel: 'Batal',
      confirmTextColor: Colors.white,
      buttonColor: AppColors.error,
      cancelTextColor: AppColors.textSecondary,
      onConfirm: () async {
        Navigator.of(context).pop();
        final success = await _controller.deleteServer(_workspaceId, _serverId);
        if (success && mounted) {
          Navigator.of(context).pop();
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppAppBar(
        title: 'Detail Server & Monitoring',
        actions: [
          // Terminal SSH shortcut
          IconButton(
            tooltip: 'Buka Terminal SSH',
            icon: const Icon(Icons.terminal_rounded, color: AppColors.primary, size: 22),
            onPressed: () {
              final server = _controller.selectedServer.value;
              if (server != null) {
                Get.toNamed(
                  '/workspaces/$_workspaceId/servers/$_serverId/terminal',
                  arguments: {
                    'workspaceId': _workspaceId,
                    'serverId': _serverId,
                    'serverName': server.name,
                    'host': server.ipAddress ?? server.hostname ?? '',
                    'username': server.username,
                  },
                  parameters: {
                    'id': _workspaceId,
                    'serverId': _serverId,
                  },
                );
              }
            },
          ),
          Obx(() {
            final isFetching = _controller.isLoadingMetrics.value;
            return IconButton(
              tooltip: 'Muat Ulang Metrik',
              icon: isFetching
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                    )
                  : const Icon(Icons.refresh_rounded, color: AppColors.primary, size: 22),
              onPressed: isFetching ? null : () => _controller.loadServerMetrics(_workspaceId, _serverId),
            );
          }),
          IconButton(
            tooltip: 'Hapus Server',
            icon: const Icon(Icons.delete_outline_rounded, color: AppColors.error),
            onPressed: _onDeleteServer,
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _onRefresh,
          color: AppColors.primary,
          backgroundColor: AppColors.surfaceElevated,
          child: Obx(() {
            if (_controller.isLoading.value && _controller.selectedServer.value == null) {
              return const Center(
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                ),
              );
            }

            final server = _controller.selectedServer.value;
            if (server == null) {
              return Center(
                child: Text(
                  _controller.errorMessage.value ?? 'Server tidak ditemukan',
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
              );
            }

            final metrics = _controller.serverMetrics.value;
            final isMetricsLoading = _controller.isLoadingMetrics.value;
            final metricsError = _controller.metricsErrorMessage.value;

            return SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 1. Server Header Card
                  _buildHeaderCard(server, metrics),

                  const SizedBox(height: 20),

                  // 2. Interactive Terminal (PTY) Section
                  const Text(
                    'Interactive Console & Terminal',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  _buildTerminalCard(server),

                  const SizedBox(height: 24),

                  // 3. Offline / Diagnostic Alert Banner
                  if (metrics != null && metrics.status == 'OFFLINE')
                    _buildOfflineAlert(metrics.error ?? 'Server tidak dapat dihubungi.')
                  else if (metricsError != null && metrics == null)
                    _buildOfflineAlert(metricsError),

                  // 3. Telemetry Section Header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Metrik Sistem Real-Time',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                      ),
                      if (metrics != null)
                        Text(
                          'Cek: ${AppFormatters.formatRelativeTime(metrics.checkedAt)}',
                          style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // 4. Metrics Grid (CPU, RAM, Disk, Load)
                  if (isMetricsLoading && metrics == null)
                    _buildMetricsSkeleton()
                  else ...[
                    _buildCPUMetricsCard(metrics?.cpu),
                    const SizedBox(height: 12),
                    _buildMemoryMetricsCard(metrics?.memory),
                    const SizedBox(height: 12),
                    _buildDiskMetricsCard(metrics?.disk),
                    const SizedBox(height: 12),
                    _buildLoadAverageCard(metrics?.load),
                  ],

                  const SizedBox(height: 24),

                  // 5. System & Network Specifications Card
                  const Text(
                    'Spesifikasi Sistem & Jaringan',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  _buildSystemSpecsCard(server, metrics),

                  const SizedBox(height: 24),

                  // 6. Services (Systemd) Management Section
                  const Text(
                    'Layanan & Services (Systemd)',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  _buildServicesCard(server),

                  const SizedBox(height: 24),

                  // 7. Docker & Container Management Section (Step 10)
                  const Text(
                    'Docker & Container Management',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  _buildDockerCard(server),

                  const SizedBox(height: 24),

                  // 8. Deployment Management Section (Step 11)
                  const Text(
                    'Deployment & Rilis Aplikasi',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  _buildDeploymentsCard(server),

                  const SizedBox(height: 24),

                  // 9. Backup Management Section (Step 12)
                  const Text(
                    'Backup Management & Cadangan Data',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  _buildBackupsCard(server),

                  const SizedBox(height: 24),

                  // 10. DevOps Agent Management Section (Step 15)
                  const Text(
                    'DevOps Agent (Execution Plane)',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  _buildAgentCard(server),

                  const SizedBox(height: 24),

                  // 11. Alerts & Notifications Section (Step 13)
                  const Text(
                    'Peringatan & Notifikasi (Alerts)',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  _buildAlertsCard(server),

                  const SizedBox(height: 24),

                  // 12. Test Connection Action
                  _buildTestConnectionSection(),
                  const SizedBox(height: 30),
                ],
              ),
            );
          }),
        ),
      ),
    );
  }

  // -------------------------------------------------------------
  // WIDGET BUILDERS
  // -------------------------------------------------------------

  Widget _buildHeaderCard(ServerModel server, ServerMetricsModel? metrics) {
    final displayStatus = metrics?.status ?? server.status;
    return AppCard(
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
                child: const Icon(Icons.dns_rounded, color: AppColors.primary, size: 26),
              ),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: server.connectionType == 'AGENT'
                          ? const Color(0xFF8A2BE2).withValues(alpha: 0.2)
                          : const Color(0xFF00B4D8).withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                        color: server.connectionType == 'AGENT'
                            ? const Color(0xFF8A2BE2)
                            : const Color(0xFF00B4D8),
                        width: 1,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          server.connectionType == 'AGENT' ? Icons.hub_rounded : Icons.terminal_rounded,
                          size: 12,
                          color: server.connectionType == 'AGENT' ? const Color(0xFFBA68C8) : const Color(0xFF90E0EF),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          server.connectionType,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: server.connectionType == 'AGENT'
                                ? const Color(0xFFBA68C8)
                                : const Color(0xFF90E0EF),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  _buildStatusBadge(displayStatus),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            server.name,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
          ),
          if (server.description != null && server.description!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              server.description!,
              style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
            ),
          ],
          const SizedBox(height: 12),
          const Divider(color: AppColors.border, height: 1),
          const SizedBox(height: 12),
          Row(
            children: [
              const Icon(Icons.layers_rounded, size: 14, color: AppColors.textMuted),
              const SizedBox(width: 6),
              Text(
                server.environment?.name ?? 'General',
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, fontWeight: FontWeight.w600),
              ),
              const Spacer(),
              Flexible(
                child: Text(
                  'ID: #${server.id.length > 8 ? server.id.substring(0, 8) : server.id}',
                  style: const TextStyle(fontSize: 11, color: AppColors.textMuted, fontFamily: 'monospace'),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildOfflineAlert(String errorMsg) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: AppCard(
        color: AppColors.errorBg,
        borderColor: AppColors.error.withValues(alpha: 0.5),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.cloud_off_rounded, color: AppColors.error, size: 24),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Server Tidak Dapat Dijangkau (OFFLINE)',
                    style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.error, fontSize: 13),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    errorMsg,
                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCPUMetricsCard(CPUMetricsModel? cpu) {
    final usage = cpu?.usagePercent;
    final cores = cpu?.cores ?? 1;
    final hasError = cpu?.error != null;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.speed_rounded, size: 18, color: AppColors.primary),
                  SizedBox(width: 8),
                  Text('CPU Usage', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                ],
              ),
              if (usage != null)
                Text(
                  AppFormatters.formatPercentage(usage),
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppColors.primary),
                ),
            ],
          ),
          const SizedBox(height: 10),
          if (hasError)
            Text(cpu!.error!, style: const TextStyle(fontSize: 12, color: AppColors.textMuted))
          else ...[
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: (usage ?? 0) / 100.0,
                minHeight: 8,
                backgroundColor: AppColors.surface,
                valueColor: AlwaysStoppedAnimation<Color>(_getBarColor(usage ?? 0)),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '$cores Core CPU',
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMemoryMetricsCard(MemoryMetricsModel? mem) {
    final usage = mem?.usagePercent;
    final usedStr = AppFormatters.formatBytes(mem?.usedBytes);
    final totalStr = AppFormatters.formatBytes(mem?.totalBytes);
    final availStr = AppFormatters.formatBytes(mem?.availableBytes);
    final hasError = mem?.error != null;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.memory_rounded, size: 18, color: AppColors.accentMint),
                  SizedBox(width: 8),
                  Text('Memory (RAM)', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                ],
              ),
              if (usage != null)
                Text(
                  AppFormatters.formatPercentage(usage),
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppColors.accentMint),
                ),
            ],
          ),
          const SizedBox(height: 10),
          if (hasError)
            Text(mem!.error!, style: const TextStyle(fontSize: 12, color: AppColors.textMuted))
          else ...[
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: (usage ?? 0) / 100.0,
                minHeight: 8,
                backgroundColor: AppColors.surface,
                valueColor: AlwaysStoppedAnimation<Color>(_getBarColor(usage ?? 0)),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('$usedStr / $totalStr', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                Text('Tersedia: $availStr', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDiskMetricsCard(DiskMetricsModel? disk) {
    final usage = disk?.usagePercent;
    final usedStr = AppFormatters.formatBytes(disk?.usedBytes);
    final totalStr = AppFormatters.formatBytes(disk?.totalBytes);
    final availStr = AppFormatters.formatBytes(disk?.availableBytes);
    final hasError = disk?.error != null;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.storage_rounded, size: 18, color: Color(0xFF00E5FF)),
                  SizedBox(width: 8),
                  Text('Disk Storage (/)', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                ],
              ),
              if (usage != null)
                Text(
                  AppFormatters.formatPercentage(usage),
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: Color(0xFF00E5FF)),
                ),
            ],
          ),
          const SizedBox(height: 10),
          if (hasError)
            Text(disk!.error!, style: const TextStyle(fontSize: 12, color: AppColors.textMuted))
          else ...[
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: (usage ?? 0) / 100.0,
                minHeight: 8,
                backgroundColor: AppColors.surface,
                valueColor: AlwaysStoppedAnimation<Color>(_getBarColor(usage ?? 0)),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('$usedStr / $totalStr', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                Text('Bebas: $availStr', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildLoadAverageCard(LoadMetricsModel? load) {
    final hasError = load?.error != null;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.stacked_line_chart_rounded, size: 18, color: AppColors.primary),
              SizedBox(width: 8),
              Text('Load Average', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 12),
          if (hasError)
            Text(load!.error!, style: const TextStyle(fontSize: 12, color: AppColors.textMuted))
          else
            Row(
              children: [
                Expanded(child: _buildLoadChip('1 min', load?.load1m?.toStringAsFixed(2) ?? '-')),
                const SizedBox(width: 10),
                Expanded(child: _buildLoadChip('5 min', load?.load5m?.toStringAsFixed(2) ?? '-')),
                const SizedBox(width: 10),
                Expanded(child: _buildLoadChip('15 min', load?.load15m?.toStringAsFixed(2) ?? '-')),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildLoadChip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          Text(value, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
        ],
      ),
    );
  }

  Widget _buildSystemSpecsCard(ServerModel server, ServerMetricsModel? metrics) {
    final sys = metrics?.system;
    final uptimeSec = metrics?.uptimeSeconds;
    final net = metrics?.network;

    String netInfo = '-';
    if (net != null && net.interfaces.isNotEmpty) {
      netInfo = net.interfaces.map((i) => '${i.name}: ${i.addresses.join(", ")}').join('\n');
    }

    return AppCard(
      child: Column(
        children: [
          _buildInfoRow('Operating System', sys?.operatingSystem ?? server.operatingSystem ?? '-'),
          const Divider(color: AppColors.border, height: 16),
          _buildInfoRow('Kernel', sys?.kernel ?? '-'),
          const Divider(color: AppColors.border, height: 16),
          _buildInfoRow('Architecture', sys?.architecture ?? '-'),
          const Divider(color: AppColors.border, height: 16),
          _buildInfoRow('Uptime', AppFormatters.formatUptime(uptimeSec)),
          const Divider(color: AppColors.border, height: 16),
          _buildInfoRow('Hostname', sys?.hostname ?? server.hostname ?? '-'),
          const Divider(color: AppColors.border, height: 16),
          _buildInfoRow('IP Address', server.ipAddress ?? '-'),
          const Divider(color: AppColors.border, height: 16),
          _buildInfoRow('Port SSH', server.sshPort.toString()),
          const Divider(color: AppColors.border, height: 16),
          _buildInfoRow('SSH Username', server.username ?? '-'),
          const Divider(color: AppColors.border, height: 16),
          _buildInfoRow('Kredensial SSH', server.hasCredential ? 'Tersimpan (${server.authType})' : 'Belum Ada'),
          if (netInfo != '-') ...[
            const Divider(color: AppColors.border, height: 16),
            _buildInfoRow('Network Interfaces', netInfo),
          ],
        ],
      ),
    );
  }

  Widget _buildTestConnectionSection() {
    return Obx(() {
      final isTesting = _controller.isTestingConnection.value;
      final testRes = _controller.connectionTestResult.value;

      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppButton(
            text: '⚡ Uji Koneksi SSH (Test Connection)',
            isLoading: isTesting,
            icon: const Icon(Icons.network_check_rounded, size: 20),
            onPressed: _onTestConnection,
          ),
          if (testRes != null) ...[
            const SizedBox(height: 12),
            AppCard(
              color: testRes.success ? AppColors.successBg : AppColors.errorBg,
              borderColor: testRes.success ? AppColors.success : AppColors.error,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        testRes.success ? Icons.check_circle_outline_rounded : Icons.error_outline_rounded,
                        color: testRes.success ? AppColors.success : AppColors.error,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        testRes.success ? 'Koneksi Berhasil (ONLINE)' : 'Koneksi Gagal (OFFLINE)',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: testRes.success ? AppColors.success : AppColors.error,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    testRes.message,
                    style: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
                  ),
                ],
              ),
            ),
          ],
        ],
      );
    });
  }

  Widget _buildMetricsSkeleton() {
    return Column(
      children: List.generate(
        3,
        (index) => Padding(
          padding: const EdgeInsets.only(bottom: 12.0),
          child: AppCard(
            child: SizedBox(
              height: 50,
              child: Center(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: const [
                    SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary)),
                    SizedBox(width: 10),
                    Text('Mengambil metrik server...', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
          ),
        ),
      ],
    );
  }

  Widget _buildStatusBadge(String status) {
    switch (status.toUpperCase()) {
      case 'ONLINE':
        return AppStatusBadge.success('ONLINE');
      case 'OFFLINE':
        return AppStatusBadge.error('OFFLINE');
      default:
        return const AppStatusBadge(label: 'UNKNOWN', color: AppColors.textMuted);
    }
  }

  Widget _buildServicesCard(ServerModel server) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.tealAccent.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.miscellaneous_services_rounded, color: Colors.tealAccent, size: 22),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Linux Systemd Services',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Kelola status & lifecycle service (Start, Stop, Restart, Reload)',
                      style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          AppButton(
            text: 'Buka Manajemen Services',
            icon: const Icon(Icons.open_in_new_rounded, size: 18, color: AppColors.primary),
            variant: AppButtonVariant.outline,
            onPressed: () {
              Get.toNamed(
                '/workspaces/$_workspaceId/servers/$_serverId/services',
                arguments: {
                  'workspace_id': _workspaceId,
                  'server_id': _serverId,
                  'server_name': server.name,
                  'user_role': 'OWNER',
                },
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildDockerCard(ServerModel server) {
    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF58A6FF).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.directions_boat_rounded, color: Color(0xFF58A6FF), size: 24),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Docker & Containers',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Kelola containers, logs, & Docker Compose cluster orchestration',
                      style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          AppButton(
            text: 'Buka Docker Dashboard',
            icon: const Icon(Icons.open_in_new_rounded, size: 18, color: Color(0xFF58A6FF)),
            variant: AppButtonVariant.outline,
            onPressed: () {
              Get.toNamed(
                '/workspaces/$_workspaceId/servers/$_serverId/docker',
                arguments: {
                  'workspace_id': _workspaceId,
                  'server_id': _serverId,
                  'server_name': server.name,
                  'role': 'OWNER',
                },
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildDeploymentsCard(ServerModel server) {
    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFFBC8CFF).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.rocket_launch_rounded, color: Color(0xFFBC8CFF), size: 24),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Deployment Management',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Rilis otomatis (Git Pull, Systemd, Compose, Build) & riwayat log deployment',
                      style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          AppButton(
            text: 'Buka Dashboard Deployment',
            icon: const Icon(Icons.open_in_new_rounded, size: 18, color: Color(0xFFBC8CFF)),
            variant: AppButtonVariant.outline,
            onPressed: () {
              Get.toNamed(
                '/workspaces/$_workspaceId/servers/$_serverId/deployments',
                arguments: {
                  'workspace_id': _workspaceId,
                  'environment_id': server.environmentId,
                  'server_id': _serverId,
                  'server_name': server.name,
                },
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildBackupsCard(ServerModel server) {
    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF336791).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.cloud_download_rounded, color: Color(0xFF58A6FF), size: 24),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Backup & Restore Metadata',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Cadangan PostgreSQL, direktori sistem berkas, Docker volume, & verifikasi integritas SHA-256',
                      style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          AppButton(
            text: 'Buka Dashboard Backup',
            icon: const Icon(Icons.open_in_new_rounded, size: 18, color: Color(0xFF58A6FF)),
            variant: AppButtonVariant.outline,
            onPressed: () {
              Get.toNamed(
                '/workspaces/$_workspaceId/servers/$_serverId/backups',
                arguments: {
                  'workspace_id': _workspaceId,
                  'environment_id': server.environmentId,
                  'server_id': _serverId,
                  'server_name': server.name,
                },
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildAlertsCard(ServerModel server) {
    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.error.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.notifications_active_outlined, color: AppColors.error, size: 24),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Peringatan & Evaluasi Metrik',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Aturan pemicu (CPU, RAM, Disk, Offline, Service), status firing, & in-app audit trail',
                      style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          AppButton(
            text: 'Buka Dashboard Alerts Server',
            icon: const Icon(Icons.open_in_new_rounded, size: 18, color: AppColors.error),
            variant: AppButtonVariant.outline,
            onPressed: () {
              Get.toNamed(
                '/workspaces/$_workspaceId/alerts',
                arguments: {
                  'workspace_id': _workspaceId,
                  'server_id': _serverId,
                  'server_name': server.name,
                },
                parameters: {
                  'id': _workspaceId,
                },
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildAgentCard(ServerModel server) {
    return Obx(() {
      final agent = _controller.agent.value;
      final isAgentLoading = _controller.isLoadingAgent.value;

      if (isAgentLoading && agent == null) {
        return const AppCard(
          padding: EdgeInsets.all(20),
          child: Center(
            child: SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
            ),
          ),
        );
      }

      final hasAgent = agent != null;

      return AppCard(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF8A2BE2).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.hub_rounded, color: Color(0xFFBA68C8), size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          const Expanded(
                            child: Text(
                              'DevOps Standalone Agent',
                              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          if (hasAgent)
                            _buildAgentStatusBadge(agent.status)
                          else
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppColors.surface,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: AppColors.border),
                              ),
                              child: const Text(
                                'NOT ENROLLED',
                                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.textMuted),
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        hasAgent
                            ? 'Outbound TLS/WebSocket connection ke control plane'
                            : 'Koneksi outbound aman dari Linux target tanpa membuka port inbound SSH.',
                        style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            if (hasAgent) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.background,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.border.withValues(alpha: 0.6)),
                ),
                child: Column(
                  children: [
                    _buildAgentInfoRow('Versi Agent', agent.agentVersion),
                    const Divider(color: AppColors.border, height: 16),
                    _buildAgentInfoRow(
                      'Heartbeat Terakhir',
                      agent.lastSeenAt != null ? AppFormatters.formatRelativeTime(agent.lastSeenAt) : 'Belum pernah',
                    ),
                    if (agent.hostname != null) ...[
                      const Divider(color: AppColors.border, height: 16),
                      _buildAgentInfoRow('Hostname Server', agent.hostname!),
                    ],
                    if (agent.operatingSystem != null) ...[
                      const Divider(color: AppColors.border, height: 16),
                      _buildAgentInfoRow('Sistem Operasi', '${agent.operatingSystem} (${agent.architecture ?? "arch"})'),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 14),

              const Text(
                'Capabilities Terdaftar:',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: [
                  _buildCapabilityChip('Monitoring', agent.hasCapability('monitoring') || agent.hasCapability('system_metrics')),
                  _buildCapabilityChip('systemd', agent.hasCapability('systemd')),
                  _buildCapabilityChip('Docker', agent.hasCapability('docker')),
                  _buildCapabilityChip('PostgreSQL', agent.hasCapability('postgresql')),
                  _buildCapabilityChip('Filesystem Backup', agent.hasCapability('filesystem_backup') || agent.hasCapability('backup')),
                ],
              ),
              const SizedBox(height: 16),

              Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  AppButton(
                    text: 'Enroll / Token Baru',
                    icon: const Icon(Icons.key_rounded, size: 16, color: AppColors.primary),
                    variant: AppButtonVariant.outline,
                    onPressed: () => _showEnrollmentDialog(context, server),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      if (agent.isActive && agent.status != 'DISABLED') ...[
                        Expanded(
                          child: AppButton(
                            text: 'Nonaktifkan',
                            icon: const Icon(Icons.pause_circle_outline_rounded, size: 16, color: AppColors.warning),
                            variant: AppButtonVariant.outline,
                            onPressed: () => _confirmDisableAgent(server),
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      Expanded(
                        child: AppButton(
                          text: 'Revoke (SSH)',
                          icon: const Icon(Icons.link_off_rounded, size: 16, color: AppColors.error),
                          variant: AppButtonVariant.outline,
                          onPressed: () => _confirmRevokeAgent(server),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ] else ...[
              AppButton(
                text: 'Generate Agent Enrollment Token',
                icon: const Icon(Icons.add_link_rounded, size: 18, color: Color(0xFFBA68C8)),
                variant: AppButtonVariant.primary,
                onPressed: () => _showEnrollmentDialog(context, server),
              ),
            ],
          ],
        ),
      );
    });
  }

  Widget _buildAgentInfoRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _buildCapabilityChip(String name, bool isSupported) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isSupported ? AppColors.success.withValues(alpha: 0.12) : AppColors.surface,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: isSupported ? AppColors.success.withValues(alpha: 0.4) : AppColors.border,
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isSupported ? Icons.check_circle_rounded : Icons.cancel_outlined,
            size: 13,
            color: isSupported ? AppColors.success : AppColors.textMuted,
          ),
          const SizedBox(width: 4),
          Text(
            name,
            style: TextStyle(
              fontSize: 11,
              fontWeight: isSupported ? FontWeight.w600 : FontWeight.normal,
              color: isSupported ? AppColors.success : AppColors.textMuted,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAgentStatusBadge(String status) {
    Color bg = AppColors.surface;
    Color fg = AppColors.textMuted;

    switch (status.toUpperCase()) {
      case 'ONLINE':
        bg = AppColors.success.withValues(alpha: 0.15);
        fg = AppColors.success;
        break;
      case 'OFFLINE':
        bg = AppColors.error.withValues(alpha: 0.15);
        fg = AppColors.error;
        break;
      case 'DISABLED':
        bg = AppColors.warning.withValues(alpha: 0.15);
        fg = AppColors.warning;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: fg),
      ),
    );
  }

  void _showEnrollmentDialog(BuildContext context, ServerModel server) async {
    final result = await _controller.generateEnrollmentToken(_workspaceId, server.id);
    if (result == null || !mounted) return;

    Get.dialog(
      Dialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.vpn_key_rounded, color: Color(0xFFBA68C8), size: 24),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'One-Time Agent Enrollment',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20, color: AppColors.textMuted),
                    onPressed: () => Get.back(),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              const Text(
                'Jalankan perintah berikut di server target Linux untuk mendaftarkan DevOps Agent. Token ini berlaku sekali pakai (single-use) selama 15 menit.',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
              const SizedBox(height: 14),

              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.background,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Command Setup:',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textMuted),
                        ),
                        InkWell(
                          onTap: () {
                            Clipboard.setData(ClipboardData(text: result.installerCommand));
                            Get.snackbar(
                              'Disalin',
                              'Perintah setup telah disalin ke clipboard.',
                              snackPosition: SnackPosition.BOTTOM,
                            );
                          },
                          child: const Row(
                            children: [
                              Icon(Icons.copy_rounded, size: 14, color: AppColors.primary),
                              SizedBox(width: 4),
                              Text('Salin', style: TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    SelectableText(
                      result.installerCommand,
                      style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: AppColors.textPrimary),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.warning.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.warning_amber_rounded, size: 16, color: AppColors.warning),
                    SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Peringatan: Token hanya ditampilkan sekali dan tidak disimpan dalam bentuk plaintext di database demi keamanan.',
                        style: TextStyle(fontSize: 11, color: AppColors.warning),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              SizedBox(
                width: double.infinity,
                child: AppButton(
                  text: 'Tutup & Selesai',
                  variant: AppButtonVariant.primary,
                  onPressed: () => Get.back(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _confirmDisableAgent(ServerModel server) {
    Get.defaultDialog(
      title: 'Nonaktifkan Agent',
      titleStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
      middleText: 'DevOps Agent pada server ini akan dinonaktifkan sementara dan tidak dapat menerima eksekusi job.',
      backgroundColor: AppColors.surface,
      textConfirm: 'Nonaktifkan',
      textCancel: 'Batal',
      confirmTextColor: Colors.white,
      buttonColor: AppColors.warning,
      cancelTextColor: AppColors.textSecondary,
      onConfirm: () async {
        Get.back();
        await _controller.disableAgent(_workspaceId, server.id);
      },
    );
  }

  void _confirmRevokeAgent(ServerModel server) {
    Get.defaultDialog(
      title: 'Cabut Kredensial Agent',
      titleStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
      middleText: 'Kredensial Agent akan dihapus permanen dan mode koneksi server akan dikembalikan ke SSH Direct.',
      backgroundColor: AppColors.surface,
      textConfirm: 'Revoke & Reset',
      textCancel: 'Batal',
      confirmTextColor: Colors.white,
      buttonColor: AppColors.error,
      cancelTextColor: AppColors.textSecondary,
      onConfirm: () async {
        Get.back();
        await _controller.revokeAgent(_workspaceId, server.id);
      },
    );
  }

  Widget _buildTerminalCard(ServerModel server) {
    return AppCard(
      gradient: AppColors.surfaceGradient,
      borderColor: AppColors.primary.withValues(alpha: 0.3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.terminal_rounded, color: AppColors.primary, size: 20),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Interactive Terminal (PTY / SSH)',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.textPrimary),
                    ),
                    Text(
                      'Akses konsol live terminal & jalankan perintah Linux langsung di HP',
                      style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          AppButton(
            text: 'Buka Terminal Konsol',
            icon: const Icon(Icons.code_rounded, size: 18),
            onPressed: () {
              Get.toNamed(
                '/workspaces/$_workspaceId/servers/$_serverId/terminal',
                arguments: {
                  'workspaceId': _workspaceId,
                  'serverId': _serverId,
                  'serverName': server.name,
                  'host': server.ipAddress ?? server.hostname ?? '',
                  'username': server.username,
                },
                parameters: {
                  'id': _workspaceId,
                  'serverId': _serverId,
                },
              );
            },
          ),
        ],
      ),
    );
  }

  Color _getBarColor(double pct) {
    if (pct >= 90) return AppColors.error;
    if (pct >= 75) return AppColors.warning;
    return AppColors.primary;
  }
}



