import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/widgets/app_bottom_sheet.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_text_field.dart';
import '../controllers/environment_controller.dart';

class CreateEnvironmentSheet extends StatefulWidget {
  final String workspaceId;

  const CreateEnvironmentSheet({super.key, required this.workspaceId});

  @override
  State<CreateEnvironmentSheet> createState() => _CreateEnvironmentSheetState();
}

class _CreateEnvironmentSheetState extends State<CreateEnvironmentSheet> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _keyController = TextEditingController();
  final _descController = TextEditingController();

  final EnvironmentController _controller = Get.find<EnvironmentController>();

  @override
  void dispose() {
    _nameController.dispose();
    _keyController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _onNameChanged(String val) {
    if (_keyController.text.isEmpty || _keyController.text == _slugify(_nameController.text.substring(0, _nameController.text.length - 1))) {
      _keyController.text = _slugify(val);
    }
  }

  String _slugify(String text) {
    return text
        .toLowerCase()
        .trim()
        .replaceAll(RegExp(r'[^a-z0-9_-]+'), '-')
        .replaceAll(RegExp(r'-+'), '-');
  }

  void _submit() async {
    if (_formKey.currentState?.validate() ?? false) {
      final success = await _controller.createEnvironment(
        workspaceId: widget.workspaceId,
        name: _nameController.text,
        key: _keyController.text,
        description: _descController.text.trim().isEmpty ? null : _descController.text.trim(),
      );

      if (success && mounted) {
        Get.back();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppBottomSheet(
      title: 'Tambah Environment',
      subtitle: 'Contoh: Production, Staging, Development',
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppTextField(
              label: 'Nama Environment',
              hint: 'e.g. Production',
              controller: _nameController,
              prefixIcon: const Icon(Icons.layers_rounded, size: 20),
              onChanged: _onNameChanged,
              validator: (val) {
                if (val == null || val.trim().isEmpty) {
                  return 'Nama environment wajib diisi';
                }
                return null;
              },
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Key / Slug (Unik)',
              hint: 'e.g. production, staging, dev',
              controller: _keyController,
              prefixIcon: const Icon(Icons.key_rounded, size: 20),
              validator: (val) {
                if (val == null || val.trim().isEmpty) {
                  return 'Key environment wajib diisi';
                }
                if (!RegExp(r'^[a-z0-9_-]+$').hasMatch(val.trim())) {
                  return 'Key hanya boleh huruf kecil, angka, - dan _';
                }
                return null;
              },
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Deskripsi (Opsional)',
              hint: 'e.g. Server utama produksi pelanggan',
              controller: _descController,
              maxLines: 2,
              prefixIcon: const Icon(Icons.notes_rounded, size: 20),
            ),
            const SizedBox(height: 24),
            Obx(
              () => AppButton(
                text: 'Simpan Environment',
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
