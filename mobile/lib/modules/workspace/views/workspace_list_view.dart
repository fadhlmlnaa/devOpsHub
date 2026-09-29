import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_bottom_sheet.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_status_badge.dart';
import '../../auth/controllers/auth_controller.dart';
import '../controllers/workspace_controller.dart';
import '../widgets/create_workspace_sheet.dart';

class WorkspaceListView extends GetView<WorkspaceController> {
  const WorkspaceListView({super.key});

  void _showCreateModal(BuildContext context) {
    AppBottomSheet.show(
      context: context,
      child: const CreateWorkspaceSheet(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authController = Get.find<AuthController>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppAppBar(
        title: 'DevOpsHub',
        showBackButton: false,
        leading: Padding(
          padding: const EdgeInsets.only(left: 16.0),
          child: Center(
            child: Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                gradient: AppColors.logoGradient,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.all_inclusive_rounded,
                size: 20,
                color: AppColors.background,
              ),
            ),
          ),
        ),
        actions: [
          IconButton(
            tooltip: 'Logout',
            icon: const Icon(Icons.logout_rounded, color: AppColors.textSecondary, size: 20),
            onPressed: () {
              Get.defaultDialog(
                title: 'Konfirmasi Logout',
                titleStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                middleText: 'Apakah Anda yakin ingin keluar dari sesi ini?',
                middleTextStyle: const TextStyle(fontSize: 14, color: AppColors.textSecondary),
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
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.textOnPrimary,
        elevation: 4,
        onPressed: () => _showCreateModal(context),
        icon: const Icon(Icons.add_rounded, size: 20),
        label: const Text(
          'Workspace Baru',
          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
        ),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.primary,
          backgroundColor: AppColors.surfaceElevated,
          onRefresh: () => controller.refreshWorkspaces(),
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              // User Greeting Header
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Obx(() {
                        final user = authController.currentUser.value;
                        final greeting = user != null ? 'Halo, ${user.name}' : 'Selamat Datang';
                        return Text(
                          greeting,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                            color: AppColors.textPrimary,
                          ),
                        );
                      }),
                      const SizedBox(height: 4),
                      const Text(
                        'Pilih workspace untuk mengelola infrastruktur & server',
                        style: TextStyle(
                          fontSize: 13,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Content / List
              Obx(() {
                if (controller.isLoading.value && controller.workspaces.isEmpty) {
                  return const SliverFillRemaining(
                    child: Center(
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                      ),
                    ),
                  );
                }

                if (controller.errorMessage.value != null && controller.workspaces.isEmpty) {
                  return SliverFillRemaining(
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24.0),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.error_outline_rounded, size: 48, color: AppColors.error),
                            const SizedBox(height: 16),
                            Text(
                              controller.errorMessage.value!,
                              textAlign: TextAlign.center,
                              style: const TextStyle(color: AppColors.textSecondary, fontSize: 14),
                            ),
                            const SizedBox(height: 20),
                            AppButton(
                              text: 'Coba Lagi',
                              width: 140,
                              onPressed: () => controller.loadWorkspaces(),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }

                if (controller.workspaces.isEmpty) {
                  return SliverFillRemaining(
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24.0),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              width: 64,
                              height: 64,
                              decoration: BoxDecoration(
                                color: AppColors.surfaceElevated,
                                shape: BoxShape.circle,
                                border: Border.all(color: AppColors.border),
                              ),
                              child: const Icon(
                                Icons.workspaces_outline,
                                size: 32,
                                color: AppColors.primary,
                              ),
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'Belum ada Workspace',
                              style: TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'Buat workspace pertama Anda untuk mulai menambahkan environment dan server.',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 13,
                                color: AppColors.textSecondary,
                              ),
                            ),
                            const SizedBox(height: 24),
                            AppButton(
                              text: 'Buat Workspace',
                              width: 200,
                              icon: const Icon(Icons.add_rounded, size: 18),
                              onPressed: () => _showCreateModal(context),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }

                return SliverPadding(
                  padding: const EdgeInsets.fromLTRB(20, 10, 20, 90),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final item = controller.workspaces[index];
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 12.0),
                          child: AppCard(
                            onTap: () => controller.selectWorkspace(item),
                            child: Row(
                              children: [
                                Container(
                                  width: 44,
                                  height: 44,
                                  decoration: BoxDecoration(
                                    color: AppColors.surface,
                                    borderRadius: BorderRadius.circular(10),
                                    border: Border.all(color: AppColors.border),
                                  ),
                                  child: const Icon(
                                    Icons.business_rounded,
                                    color: AppColors.primary,
                                    size: 22,
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Expanded(
                                            child: Text(
                                              item.name,
                                              style: const TextStyle(
                                                fontSize: 15,
                                                fontWeight: FontWeight.w700,
                                                color: AppColors.textPrimary,
                                              ),
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          const SizedBox(width: 8),
                                          AppStatusBadge.role(item.role),
                                        ],
                                      ),
                                      if (item.description != null &&
                                          item.description!.isNotEmpty) ...[
                                        const SizedBox(height: 4),
                                        Text(
                                          item.description!,
                                          style: const TextStyle(
                                            fontSize: 12,
                                            color: AppColors.textSecondary,
                                          ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ],
                                      const SizedBox(height: 6),
                                      Row(
                                        children: [
                                          const Icon(
                                            Icons.schedule_rounded,
                                            size: 13,
                                            color: AppColors.textMuted,
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            item.timezone,
                                            style: const TextStyle(
                                              fontSize: 11,
                                              color: AppColors.textMuted,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 8),
                                const Icon(
                                  Icons.chevron_right_rounded,
                                  color: AppColors.textMuted,
                                  size: 20,
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                      childCount: controller.workspaces.length,
                    ),
                  ),
                );
              }),
            ],
          ),
        ),
      ),
    );
  }
}
