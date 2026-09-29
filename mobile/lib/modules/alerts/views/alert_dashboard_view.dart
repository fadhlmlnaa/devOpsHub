import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../data/models/alert_model.dart';
import '../controllers/alert_controller.dart';
import '../controllers/alert_rule_controller.dart';
import '../controllers/notification_controller.dart';
import '../widgets/alert_card.dart';
import '../widgets/alert_rule_card.dart';
import 'alert_detail_view.dart';
import 'alert_rule_form_view.dart';
import 'notification_list_view.dart';

class AlertDashboardView extends StatefulWidget {
  final String workspaceId;
  final String? serverId;

  const AlertDashboardView({
    super.key,
    required this.workspaceId,
    this.serverId,
  });

  @override
  State<AlertDashboardView> createState() => _AlertDashboardViewState();
}

class _AlertDashboardViewState extends State<AlertDashboardView> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late AlertController alertCtrl;
  late AlertRuleController ruleCtrl;
  late NotificationController notifCtrl;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    alertCtrl = Get.find<AlertController>();
    ruleCtrl = Get.find<AlertRuleController>();
    notifCtrl = Get.find<NotificationController>();

    alertCtrl.initWorkspace(widget.workspaceId, serverId: widget.serverId);
    ruleCtrl.initWorkspace(widget.workspaceId, serverId: widget.serverId);
    notifCtrl.initWorkspace(widget.workspaceId);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(
          'Peringatan & Notifikasi',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        backgroundColor: AppColors.surface,
        elevation: 0,
        actions: [
          // Manual Evaluation trigger
          Obx(() => IconButton(
                icon: alertCtrl.isEvaluating.value
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                      )
                    : const Icon(Icons.sync_rounded, color: AppColors.primary),
                tooltip: 'Evaluasi Alert Sekarang',
                onPressed: alertCtrl.isEvaluating.value
                    ? null
                    : () => alertCtrl.triggerManualEvaluation(),
              )),
          // Notification Bell with Badge
          Obx(() {
            final unread = notifCtrl.unreadCount.value;
            return Stack(
              alignment: Alignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.notifications_outlined, color: AppColors.textPrimary),
                  tooltip: 'Inbox Notifikasi',
                  onPressed: () {
                    Get.to(() => NotificationListView(workspaceId: widget.workspaceId));
                  },
                ),
                if (unread > 0)
                  Positioned(
                    top: 10,
                    right: 10,
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
          }),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.primary,
          indicatorWeight: 3,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textMuted,
          tabs: [
            Obx(() {
              final firing = alertCtrl.firingCount;
              return Tab(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('Alert'),
                    if (firing > 0) ...[
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.error,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '$firing',
                          style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ],
                ),
              );
            }),
            const Tab(text: 'Aturan Rules'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildAlertsTab(),
          _buildRulesTab(),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.textOnPrimary,
        icon: const Icon(Icons.add),
        label: const Text('Tambah Aturan', style: TextStyle(fontWeight: FontWeight.bold)),
        onPressed: () async {
          final res = await Get.to(() => AlertRuleFormView(
                workspaceId: widget.workspaceId,
                serverId: widget.serverId,
              ));
          if (res == true) {
            ruleCtrl.fetchRules();
          }
        },
      ),
    );
  }

  Widget _buildAlertsTab() {
    return RefreshIndicator(
      onRefresh: () async {
        await alertCtrl.fetchAlerts();
      },
      color: AppColors.primary,
      child: Column(
        children: [
          // Filter Chips (Status & Severity)
          Container(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            color: AppColors.surface,
            child: Column(
              children: [
                // Status filter
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Obx(() => Row(
                        children: [
                          _buildFilterChip('Semua Status', 'ALL', alertCtrl.selectedStatus.value, (val) {
                            alertCtrl.setStatusFilter(val);
                          }),
                          const SizedBox(width: 8),
                          _buildFilterChip('🔥 Firing', 'FIRING', alertCtrl.selectedStatus.value, (val) {
                            alertCtrl.setStatusFilter(val);
                          }, activeColor: AppColors.error),
                          const SizedBox(width: 8),
                          _buildFilterChip('✅ Resolved', 'RESOLVED', alertCtrl.selectedStatus.value, (val) {
                            alertCtrl.setStatusFilter(val);
                          }, activeColor: AppColors.success),
                          const SizedBox(width: 12),
                          Container(width: 1, height: 20, color: AppColors.border),
                          const SizedBox(width: 12),
                          _buildFilterChip('Semua Severity', 'ALL', alertCtrl.selectedSeverity.value, (val) {
                            alertCtrl.setSeverityFilter(val);
                          }),
                          const SizedBox(width: 8),
                          _buildFilterChip('🔴 Critical', 'CRITICAL', alertCtrl.selectedSeverity.value, (val) {
                            alertCtrl.setSeverityFilter(val);
                          }, activeColor: AppColors.error),
                          const SizedBox(width: 8),
                          _buildFilterChip('🟠 Warning', 'WARNING', alertCtrl.selectedSeverity.value, (val) {
                            alertCtrl.setSeverityFilter(val);
                          }, activeColor: AppColors.warning),
                          const SizedBox(width: 8),
                          _buildFilterChip('🔵 Info', 'INFO', alertCtrl.selectedSeverity.value, (val) {
                            alertCtrl.setSeverityFilter(val);
                          }, activeColor: AppColors.info),
                        ],
                      )),
                ),
              ],
            ),
          ),

          // Alert list content
          Expanded(
            child: Obx(() {
              if (alertCtrl.isLoading.value) {
                return const Center(child: CircularProgressIndicator(color: AppColors.primary));
              }

              if (alertCtrl.errorMessage.isNotEmpty) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: AppColors.error),
                        const SizedBox(height: 12),
                        Text(
                          alertCtrl.errorMessage.value,
                          style: const TextStyle(color: AppColors.textSecondary),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () => alertCtrl.fetchAlerts(),
                          child: const Text('Coba Lagi'),
                        ),
                      ],
                    ),
                  ),
                );
              }

              final list = alertCtrl.filteredAlerts;
              if (list.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.check_circle_outline, size: 64, color: AppColors.textMuted.withValues(alpha: 0.5)),
                      const SizedBox(height: 12),
                      const Text(
                        'Tidak ada alert yang sesuai filter',
                        style: TextStyle(color: AppColors.textSecondary, fontSize: 15, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Semua sistem berjalan dengan normal.',
                        style: TextStyle(color: AppColors.textMuted, fontSize: 13),
                      ),
                    ],
                  ),
                );
              }

              return ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: list.length,
                itemBuilder: (context, index) {
                  final alert = list[index];
                  return AlertCard(
                    alert: alert,
                    onTap: () {
                      Get.to(() => AlertDetailView(
                            workspaceId: widget.workspaceId,
                            alertId: alert.id,
                          ));
                    },
                  );
                },
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildRulesTab() {
    return RefreshIndicator(
      onRefresh: () async {
        await ruleCtrl.fetchRules();
      },
      color: AppColors.primary,
      child: Obx(() {
        if (ruleCtrl.isLoading.value) {
          return const Center(child: CircularProgressIndicator(color: AppColors.primary));
        }

        if (ruleCtrl.errorMessage.isNotEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: AppColors.error),
                  const SizedBox(height: 12),
                  Text(
                    ruleCtrl.errorMessage.value,
                    style: const TextStyle(color: AppColors.textSecondary),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => ruleCtrl.fetchRules(),
                    child: const Text('Coba Lagi'),
                  ),
                ],
              ),
            ),
          );
        }

        final rules = ruleCtrl.rules;
        if (rules.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.tune_outlined, size: 64, color: AppColors.textMuted.withValues(alpha: 0.5)),
                const SizedBox(height: 12),
                const Text(
                  'Belum ada aturan alert',
                  style: TextStyle(color: AppColors.textSecondary, fontSize: 15, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Tekan tombol "Tambah Aturan" untuk membuat aturan monitoring.',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
          itemCount: rules.length,
          itemBuilder: (context, index) {
            final rule = rules[index];
            return AlertRuleCard(
              rule: rule,
              onToggleEnabled: (_) => ruleCtrl.toggleRuleStatus(rule),
              onEdit: () async {
                final res = await Get.to(() => AlertRuleFormView(
                      workspaceId: widget.workspaceId,
                      serverId: widget.serverId,
                      rule: rule,
                    ));
                if (res == true) {
                  ruleCtrl.fetchRules();
                }
              },
              onDelete: () => _confirmDeleteRule(rule),
            );
          },
        );
      }),
    );
  }

  Widget _buildFilterChip(String label, String value, String selectedValue, ValueChanged<String> onSelected, {Color? activeColor}) {
    final isSelected = selectedValue == value;
    final color = activeColor ?? AppColors.primary;
    return GestureDetector(
      onTap: () => onSelected(value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? color.withValues(alpha: 0.2) : AppColors.surfaceElevated,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? color : AppColors.border,
            width: 1,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? color : AppColors.textSecondary,
            fontSize: 12,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  void _confirmDeleteRule(AlertRuleModel rule) {
    Get.dialog(
      AlertDialog(
        backgroundColor: AppColors.surfaceElevated,
        title: const Text('Hapus Aturan Alert?', style: TextStyle(color: AppColors.textPrimary)),
        content: Text(
          'Apakah Anda yakin ingin menghapus aturan "${rule.name}"? Riwayat alert yang sudah tercatat tidak akan dihapus.',
          style: const TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Batal', style: TextStyle(color: AppColors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
            onPressed: () async {
              Get.back();
              await ruleCtrl.deleteRule(rule.id);
            },
            child: const Text('Hapus', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
