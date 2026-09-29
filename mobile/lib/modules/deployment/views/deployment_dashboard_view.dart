import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/deployment_controller.dart';
import '../controllers/deployment_config_controller.dart';
import '../widgets/deployment_card.dart';
import '../widgets/deployment_config_card.dart';
import '../widgets/deployment_confirm_sheet.dart';
import 'deployment_log_view.dart';
import 'deployment_config_form_view.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../data/models/deployment_model.dart';

class DeploymentDashboardView extends StatefulWidget {
  const DeploymentDashboardView({super.key});

  @override
  State<DeploymentDashboardView> createState() => _DeploymentDashboardViewState();
}

class _DeploymentDashboardViewState extends State<DeploymentDashboardView>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late final DeploymentController _depCtrl;
  late final DeploymentConfigController _cfgCtrl;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _depCtrl = Get.put(DeploymentController());
    _cfgCtrl = Get.put(DeploymentConfigController());
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _showDeployConfirmation(DeploymentConfigModel config) {
    Get.bottomSheet(
      DeploymentConfirmSheet(
        config: config,
        onConfirm: () async {
          Get.back(); // close sheet
          final success = await _depCtrl.triggerDeployment(config, confirm: true);
          if (success) {
            _tabController.animateTo(0); // switch to history
          }
        },
      ),
      isScrollControlled: true,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppAppBar(
        title: 'Deployment Management',
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Colors.white),
            onPressed: () {
              _depCtrl.refreshDeployments();
              _cfgCtrl.refreshConfigs();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Segmented Tab Bar
          Container(
            color: AppColors.surfaceCard,
            child: TabBar(
              controller: _tabController,
              indicatorColor: AppColors.primary,
              indicatorWeight: 3,
              labelColor: AppColors.primary,
              unselectedLabelColor: AppColors.textSecondary,
              labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              tabs: const [
                Tab(
                  icon: Icon(Icons.history_rounded, size: 20),
                  text: 'Riwayat Deploy',
                ),
                Tab(
                  icon: Icon(Icons.settings_suggest_rounded, size: 20),
                  text: 'Konfigurasi App',
                ),
              ],
            ),
          ),

          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildHistoryTab(),
                _buildConfigsTab(),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: Obx(() {
        if (_tabController.index == 1 || _cfgCtrl.configs.isEmpty) {
          return FloatingActionButton.extended(
            backgroundColor: AppColors.primary,
            icon: const Icon(Icons.add_rounded, color: Colors.black),
            label: const Text(
              'Tambah Konfigurasi',
              style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
            ),
            onPressed: () async {
              final result = await Get.to(() => DeploymentConfigFormView(
                    workspaceId: _cfgCtrl.workspaceId,
                    environmentId: _cfgCtrl.environmentId,
                    serverId: _cfgCtrl.serverId,
                  ));
              if (result == true) {
                _cfgCtrl.refreshConfigs();
              }
            },
          );
        }
        return const SizedBox.shrink();
      }),
    );
  }

  Widget _buildHistoryTab() {
    return Obx(() {
      if (_depCtrl.isLoading.value) {
        return const Center(child: CircularProgressIndicator(color: AppColors.primary));
      }

      if (_depCtrl.errorMessage.isNotEmpty) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline_rounded, color: AppColors.error, size: 48),
                const SizedBox(height: 12),
                Text(
                  _depCtrl.errorMessage.value,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => _depCtrl.fetchDeployments(),
                  child: const Text('Coba Lagi'),
                ),
              ],
            ),
          ),
        );
      }

      if (_depCtrl.deployments.isEmpty) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceCard,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(Icons.rocket_outlined, color: AppColors.textSecondary, size: 48),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Belum Ada Riwayat Deployment',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Eksekusi deployment dari tab Konfigurasi App untuk memulai rilis aplikasi.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        );
      }

      return RefreshIndicator(
        onRefresh: _depCtrl.refreshDeployments,
        color: AppColors.primary,
        child: ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: _depCtrl.deployments.length,
          separatorBuilder: (context, index) => const SizedBox(height: 12),
          itemBuilder: (context, index) {
            final item = _depCtrl.deployments[index];
            return DeploymentCard(
              deployment: item,
              onTap: () {
                Get.to(() => DeploymentLogView(
                      workspaceId: _depCtrl.workspaceId,
                      deployment: item,
                    ));
              },
            );
          },
        ),
      );
    });
  }

  Widget _buildConfigsTab() {
    return Obx(() {
      if (_cfgCtrl.isLoading.value) {
        return const Center(child: CircularProgressIndicator(color: AppColors.primary));
      }

      if (_cfgCtrl.errorMessage.isNotEmpty) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline_rounded, color: AppColors.error, size: 48),
                const SizedBox(height: 12),
                Text(
                  _cfgCtrl.errorMessage.value,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => _cfgCtrl.fetchConfigs(),
                  child: const Text('Coba Lagi'),
                ),
              ],
            ),
          ),
        );
      }

      if (_cfgCtrl.configs.isEmpty) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceCard,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(Icons.tune_rounded, color: AppColors.textSecondary, size: 48),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Belum Ada Konfigurasi Terdaftar',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Daftarkan konfigurasi deployment (Systemd / Compose) untuk server Anda.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        );
      }

      return RefreshIndicator(
        onRefresh: _cfgCtrl.refreshConfigs,
        color: AppColors.primary,
        child: ListView.separated(
          padding: const EdgeInsets.only(left: 16, right: 16, top: 16, bottom: 80),
          itemCount: _cfgCtrl.configs.length,
          separatorBuilder: (context, index) => const SizedBox(height: 12),
          itemBuilder: (context, index) {
            final config = _cfgCtrl.configs[index];
            return DeploymentConfigCard(
              config: config,
              isDeploying: _depCtrl.isDeploying.value,
              onDeploy: () => _showDeployConfirmation(config),
              onEdit: () async {
                final res = await Get.to(() => DeploymentConfigFormView(
                      workspaceId: _cfgCtrl.workspaceId,
                      environmentId: config.environmentId,
                      serverId: config.serverId,
                      config: config,
                    ));
                if (res == true) _cfgCtrl.refreshConfigs();
              },
              onDelete: () async {
                final confirm = await Get.dialog<bool>(
                  AlertDialog(
                    backgroundColor: AppColors.surfaceCard,
                    title: const Text('Hapus Konfigurasi?', style: TextStyle(color: Colors.white)),
                    content: Text(
                      'Apakah Anda yakin ingin menghapus konfigurasi "${config.name}"?',
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Get.back(result: false),
                        child: const Text('Batal'),
                      ),
                      TextButton(
                        onPressed: () => Get.back(result: true),
                        child: const Text('Hapus', style: TextStyle(color: AppColors.error)),
                      ),
                    ],
                  ),
                );
                if (confirm == true) {
                  _cfgCtrl.deleteConfig(config.id);
                }
              },
            );
          },
        ),
      );
    });
  }
}
