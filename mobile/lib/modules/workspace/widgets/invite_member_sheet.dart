import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_bottom_sheet.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_text_field.dart';
import '../controllers/workspace_controller.dart';

class InviteMemberSheet extends StatefulWidget {
  final String workspaceId;

  const InviteMemberSheet({super.key, required this.workspaceId});

  @override
  State<InviteMemberSheet> createState() => _InviteMemberSheetState();
}

class _InviteMemberSheetState extends State<InviteMemberSheet> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  String _selectedRole = 'DEVELOPER';

  final WorkspaceController _controller = Get.find<WorkspaceController>();

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  void _submit() async {
    if (_formKey.currentState?.validate() ?? false) {
      final success = await _controller.addMember(
        workspaceId: widget.workspaceId,
        email: _emailController.text,
        role: _selectedRole,
      );

      if (success && mounted) {
        Navigator.of(context).pop();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppBottomSheet(
      title: 'Undang Anggota',
      subtitle: 'Tambahkan anggota baru dan tentukan hak aksesnya',
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppTextField(
                label: 'Email Pengguna',
                hint: 'user@example.com',
                keyboardType: TextInputType.emailAddress,
                controller: _emailController,
                prefixIcon: const Icon(Icons.email_outlined, size: 20),
                validator: (val) {
                  if (val == null || val.trim().isEmpty) {
                    return 'Email wajib diisi';
                  }
                  if (!val.contains('@') || !val.contains('.')) {
                    return 'Format email tidak valid';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Pilih Role Anggota',
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
                ],
              ),
              const SizedBox(height: 24),
              Obx(
                () => AppButton(
                  text: 'Kirim Undangan / Tambahkan',
                  isLoading: _controller.isActionInProgress.value,
                  icon: const Icon(Icons.person_add_rounded, size: 20),
                  onPressed: _submit,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
