import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_status_badge.dart';
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
        title: 'Detail Server',
        actions: [
          IconButton(
            tooltip: 'Hapus Server',
            icon: const Icon(Icons.delete_outline_rounded, color: AppColors.error),
            onPressed: _onDeleteServer,
          ),
        ],
      ),
      body: SafeArea(
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

          return SingleChildScrollView(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Server Header Card
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
                            child: const Icon(Icons.dns_rounded, color: AppColors.primary, size: 26),
                          ),
                          _buildStatusBadge(server.status),
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
                ),

                const SizedBox(height: 20),

                // Connection Test Action
                Obx(() {
                  final isTesting = _controller.isTestingConnection.value;
                  final testRes = _controller.connectionTestResult.value;

                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      AppButton(
                        text: 'Uji Koneksi SSH (Test Connection)',
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
                              if (testRes.serverInfo != null) ...[
                                const SizedBox(height: 10),
                                const Divider(color: AppColors.border, height: 1),
                                const SizedBox(height: 10),
                                _buildInfoRow('Hostname', testRes.serverInfo!['hostname']?.toString() ?? '-'),
                                _buildInfoRow('Operating System', testRes.serverInfo!['operating_system']?.toString() ?? '-'),
                                _buildInfoRow('Kernel', testRes.serverInfo!['kernel']?.toString() ?? '-'),
                                _buildInfoRow('Architecture', testRes.serverInfo!['architecture']?.toString() ?? '-'),
                                _buildInfoRow('Uptime', testRes.serverInfo!['uptime']?.toString() ?? '-'),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ],
                  );
                }),

                const SizedBox(height: 24),
                const Text(
                  'Informasi Server & Jaringan',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                ),
                const SizedBox(height: 12),

                AppCard(
                  child: Column(
                    children: [
                      _buildInfoRow('IP Address', server.ipAddress ?? '-'),
                      const Divider(color: AppColors.border, height: 16),
                      _buildInfoRow('Hostname', server.hostname ?? '-'),
                      const Divider(color: AppColors.border, height: 16),
                      _buildInfoRow('Port SSH', server.sshPort.toString()),
                      const Divider(color: AppColors.border, height: 16),
                      _buildInfoRow('Default Username', server.username ?? '-'),
                      const Divider(color: AppColors.border, height: 16),
                      _buildInfoRow('Operating System', server.operatingSystem ?? '-'),
                      const Divider(color: AppColors.border, height: 16),
                      _buildInfoRow('Kredensial SSH', server.hasCredential ? 'Tersimpan (${server.authType})' : 'Belum Ada'),
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

  Widget _buildInfoRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
        Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
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
}
