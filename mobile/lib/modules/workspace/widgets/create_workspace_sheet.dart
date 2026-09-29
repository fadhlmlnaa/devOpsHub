import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_bottom_sheet.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_text_field.dart';
import '../controllers/workspace_controller.dart';

class CreateWorkspaceSheet extends StatefulWidget {
  const CreateWorkspaceSheet({super.key});

  @override
  State<CreateWorkspaceSheet> createState() => _CreateWorkspaceSheetState();
}

class _CreateWorkspaceSheetState extends State<CreateWorkspaceSheet> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  String _selectedTimezone = 'Asia/Jakarta';

  final WorkspaceController _controller = Get.find<WorkspaceController>();

  final List<String> _timezones = [
    'Asia/Jakarta',
    'Asia/Makassar',
    'Asia/Jayapura',
    'Asia/Singapore',
    'Asia/Tokyo',
    'UTC',
    'America/New_York',
    'Europe/London',
  ];

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _submit() async {
    if (_formKey.currentState?.validate() ?? false) {
      final success = await _controller.createWorkspace(
        name: _nameController.text,
        description: _descriptionController.text.trim().isEmpty
            ? null
            : _descriptionController.text.trim(),
        timezone: _selectedTimezone,
      );

      if (success && mounted) {
        Navigator.of(context).pop();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppBottomSheet(
      title: 'Buat Workspace Baru',
      subtitle: 'Anda akan otomatis menjadi OWNER di workspace ini.',
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppTextField(
              label: 'Nama Workspace',
              hint: 'e.g. PT Bintang Teknologi',
              controller: _nameController,
              prefixIcon: const Icon(Icons.business_rounded, size: 20),
              validator: (val) {
                if (val == null || val.trim().isEmpty) {
                  return 'Nama workspace wajib diisi';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            AppTextField(
              label: 'Deskripsi (Opsional)',
              hint: 'e.g. Infrastruktur cloud & server produksi',
              controller: _descriptionController,
              maxLines: 2,
              prefixIcon: const Icon(Icons.notes_rounded, size: 20),
            ),
            const SizedBox(height: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Timezone',
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
                      value: _selectedTimezone,
                      isExpanded: true,
                      dropdownColor: AppColors.surfaceElevated,
                      icon: const Icon(Icons.arrow_drop_down_rounded, color: AppColors.textSecondary),
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                      items: _timezones.map((tz) {
                        return DropdownMenuItem<String>(
                          value: tz,
                          child: Row(
                            children: [
                              const Icon(Icons.schedule_rounded, size: 18, color: AppColors.primary),
                              const SizedBox(width: 10),
                              Text(tz),
                            ],
                          ),
                        );
                      }).toList(),
                      onChanged: (val) {
                        if (val != null) {
                          setState(() {
                            _selectedTimezone = val;
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
                text: 'Buat Workspace',
                isLoading: _controller.isCreating.value,
                icon: const Icon(Icons.add_rounded, size: 20),
                onPressed: _submit,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
