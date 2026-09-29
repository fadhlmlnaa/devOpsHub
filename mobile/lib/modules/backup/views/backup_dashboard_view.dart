import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/backup_controller.dart';
import '../controllers/backup_config_controller.dart';
import '../widgets/backup_card.dart';
import '../widgets/backup_config_card.dart';
import '../widgets/backup_confirm_sheet.dart';
import 'backup_detail_view.dart';
import 'backup_config_form_view.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../data/models/backup_model.dart';

class BackupDashboardView extends StatefulWidget {
  const BackupDashboardView({super.key});

  @override
  State<BackupDashboardView> createState() => _BackupDashboardViewState();
}

class _BackupDashboardViewState extends State<BackupDashboardView>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late final BackupController _backupCtrl;
  late final BackupConfigController _cfgCtrl;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _backupCtrl = Get.isRegistered<BackupController>()
        ? Get.find<BackupController>()
        : Get.put(BackupController());
    _cfgCtrl = Get.isRegistered<BackupConfigController>()
        ? Get.find<BackupConfigController>()
        : Get.put(BackupConfigController());
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _showBackupConfirmation(BackupConfigModel config) {
    Get.bottomSheet(
      BackupConfirmSheet(
        config: config,
        onConfirm: () async {
          Get.back(); // close sheet
          final success = await _backupCtrl.triggerBackup(config, confirm: true);
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
        title: 'Backup Management',
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Colors.white),
            onPressed: () {
              _backupCtrl.refreshBackups();
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
                  text: 'Riwayat Backup',
                ),
                Tab(
                  icon: Icon(Icons.settings_suggest_rounded, size: 20),
                  text: 'Konfigurasi Target',
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
              final result = await Get.to(() => BackupConfigFormView(
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
      if (_backupCtrl.isLoading.value) {
        return const Center(child: CircularProgressIndicator(color: AppColors.primary));
      }

      if (_backupCtrl.errorMessage.isNotEmpty) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline_rounded, color: AppColors.error, size: 48),
                const SizedBox(height: 12),
                Text(
                  _backupCtrl.errorMessage.value,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => _backupCtrl.fetchBackups(),
                  child: const Text('Coba Lagi'),
                ),
              ],
            ),
          ),
        );
      }

      if (_backupCtrl.backups.isEmpty) {
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
                  child: const Icon(Icons.cloud_download_outlined, color: AppColors.textSecondary, size: 48),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Belum Ada Riwayat Backup',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Picu proses backup dari tab Konfigurasi Target untuk membuat cadangan data server Anda.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        );
      }

      return RefreshIndicator(
        onRefresh: _backupCtrl.refreshBackups,
        color: AppColors.primary,
        child: ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: _backupCtrl.backups.length,
          separatorBuilder: (context, index) => const SizedBox(height: 12),
          itemBuilder: (context, index) {
            final item = _backupCtrl.backups[index];
            return BackupCard(
              backup: item,
              onTap: () {
                Get.to(() => BackupDetailView(
                      workspaceId: _backupCtrl.workspaceId,
                      backup: item,
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
                  'Daftarkan target backup (PostgreSQL / Filesystem / Docker Volume) untuk server Anda.',
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
            return BackupConfigCard(
              config: config,
              isRunning: _backupCtrl.isRunningBackup.value,
              onRun: () => _showBackupConfirmation(config),
              onEdit: () async {
                final res = await Get.to(() => BackupConfigFormView(
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
