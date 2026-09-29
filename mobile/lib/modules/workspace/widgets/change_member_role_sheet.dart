import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_bottom_sheet.dart';
import '../../../core/widgets/app_button.dart';
import '../../../data/models/workspace_member_model.dart';
import '../controllers/workspace_controller.dart';

class ChangeMemberRoleSheet extends StatefulWidget {
  final String workspaceId;
  final WorkspaceMemberModel member;

  const ChangeMemberRoleSheet({
    super.key,
    required this.workspaceId,
    required this.member,
  });

  @override
  State<ChangeMemberRoleSheet> createState() => _ChangeMemberRoleSheetState();
}

class _ChangeMemberRoleSheetState extends State<ChangeMemberRoleSheet> {
  late String _selectedRole;
  final WorkspaceController _controller = Get.find<WorkspaceController>();

  @override
  void initState() {
    super.initState();
    final role = widget.member.role.toUpperCase();
    _selectedRole = ['ADMIN', 'DEVELOPER', 'VIEWER'].contains(role) ? role : 'DEVELOPER';
  }

  void _submit() async {
    final success = await _controller.updateMemberRole(
      workspaceId: widget.workspaceId,
      userId: widget.member.userId,
      newRole: _selectedRole,
    );

    if (success && mounted) {
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppBottomSheet(
      title: 'Ubah Role Anggota',
      subtitle: widget.member.userName ?? widget.member.userEmail ?? widget.member.userId,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Pilih Role Baru',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: AppColors.surfaceElevated,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedRole,
                  isExpanded: true,
                  dropdownColor: AppColors.surfaceElevated,
                  icon: const Icon(Icons.arrow_drop_down_rounded, color: AppColors.textSecondary),
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: 'ADMIN',
                      child: Text('ADMIN - Akses Penuh Konfigurasi & Member'),
                    ),
                    DropdownMenuItem(
                      value: 'DEVELOPER',
                      child: Text('DEVELOPER - Akses Server & Deployment'),
                    ),
                    DropdownMenuItem(
                      value: 'VIEWER',
                      child: Text('VIEWER - Hanya Monitoring & Read-Only'),
                    ),
                  ],
                  onChanged: (val) {
                    if (val != null) {
                      setState(() {
                        _selectedRole = val;
                      });
                    }
                  },
                ),
              ),
            ),
            const SizedBox(height: 24),
            Obx(
              () => AppButton(
                text: 'Simpan Perubahan Role',
                isLoading: _controller.isActionInProgress.value,
                icon: const Icon(Icons.check_rounded, size: 20),
                onPressed: _submit,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
