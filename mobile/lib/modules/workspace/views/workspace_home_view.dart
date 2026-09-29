import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_status_badge.dart';
import '../../auth/controllers/auth_controller.dart';
import '../controllers/workspace_controller.dart';

class WorkspaceHomeView extends GetView<WorkspaceController> {
  const WorkspaceHomeView({super.key});

  @override
  Widget build(BuildContext context) {
    final authController = Get.find<AuthController>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppAppBar(
        title: 'Workspace Home',
        actions: [
          IconButton(
            tooltip: 'Ganti Workspace',
            icon: const Icon(
              Icons.swap_horiz_rounded,
              color: AppColors.primary,
            ),
            onPressed: () => Get.back(),
          ),
          IconButton(
            tooltip: 'Logout',
            icon: const Icon(
              Icons.logout_rounded,
              color: AppColors.textSecondary,
              size: 20,
            ),
            onPressed: () {
              Get.defaultDialog(
                title: 'Konfirmasi Logout',
                titleStyle: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
                middleText: 'Apakah Anda yakin ingin keluar dari sesi ini?',
                middleTextStyle: const TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
                backgroundColor: AppColors.surface,
                textConfirm: 'Logout',
                textCancel: 'Batal',
                confirmTextColor: Colors.white,
                buttonColor: AppColors.error,
                cancelTextColor: AppColors.textSecondary,
                onConfirm: () {
                  Get.back();
                  authController.logout();
                },
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Obx(() {
          final workspace = controller.selectedWorkspace.value;
          if (workspace == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    'Tidak ada workspace yang dipilih',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: () => Get.offNamed('/workspaces'),
                    child: const Text('Pilih Workspace'),
                  ),
                ],
              ),
            );
          }

          return SingleChildScrollView(
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
                            child: const Icon(
                              Icons.apartment_rounded,
                              color: AppColors.primary,
                              size: 26,
                            ),
                          ),
                          AppStatusBadge.role(workspace.role),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Text(
                        workspace.name,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      if (workspace.description != null &&
                          workspace.description!.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          workspace.description!,
                          style: const TextStyle(
                            fontSize: 13,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                      const SizedBox(height: 12),
                      const Divider(color: AppColors.border, height: 1),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          const Icon(
                            Icons.schedule_rounded,
                            size: 14,
                            color: AppColors.textMuted,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            workspace.timezone,
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary,
                            ),
                          ),
                          const Spacer(),
                          Flexible(
                            child: Text(
                              'ID: #${workspace.id.length > 8 ? workspace.id.substring(0, 8) : workspace.id}',
                              style: const TextStyle(
                                fontSize: 11,
                                color: AppColors.textMuted,
                                fontFamily: 'monospace',
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // Coming Soon Modules Placeholder Section
                const Text(
                  'Environment & Server Management',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 12),

                AppCard(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      vertical: 24.0,
                      horizontal: 16.0,
                    ),
                    child: Column(
                      children: [
                        Container(
                          width: 56,
                          height: 56,
                          decoration: BoxDecoration(
                            color: AppColors.surface,
                            shape: BoxShape.circle,
                            border: Border.all(color: AppColors.border),
                          ),
                          child: const Icon(
                            Icons.dns_rounded,
                            size: 28,
                            color: AppColors.accentMint,
                          ),
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'Coming Soon',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Server management, environments, SSH, monitoring & deployments akan diimplementasikan pada langkah-langkah berikutnya.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 13,
                            color: AppColors.textSecondary,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16),

                // Placeholder Quick Navigation Grid
                Row(
                  children: [
                    Expanded(
                      child: _buildPlaceholderCard(
                        icon: Icons.layers_rounded,
                        title: 'Environments',
                        subtitle: 'Step 06',
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildPlaceholderCard(
                        icon: Icons.storage_rounded,
                        title: 'Servers',
                        subtitle: 'Step 07',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: _buildPlaceholderCard(
                        icon: Icons.terminal_rounded,
                        title: 'SSH Terminal',
                        subtitle: 'Step 08',
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildPlaceholderCard(
                        icon: Icons.notifications_none_rounded,
                        title: 'Alerts',
                        subtitle: 'Step 09',
                      ),
                    ),
                  ],
                ),
              ],
            ),
          );
        }),
      ),
    );
  }

  Widget _buildPlaceholderCard({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return AppCard(
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppColors.textMuted),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textSecondary,
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 11,
                    color: AppColors.textMuted,
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
