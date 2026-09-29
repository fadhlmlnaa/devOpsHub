import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_text_field.dart';
import '../../environment/controllers/environment_controller.dart';
import '../controllers/docker_compose_controller.dart';

class CreateComposeSheet extends StatefulWidget {
  final String workspaceId;
  final String serverId;

  const CreateComposeSheet({
    super.key,
    required this.workspaceId,
    required this.serverId,
  });

  @override
  State<CreateComposeSheet> createState() => _CreateComposeSheetState();
}

class _CreateComposeSheetState extends State<CreateComposeSheet> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _projectController = TextEditingController();
  final _dirController = TextEditingController();
  final _fileController = TextEditingController(text: 'docker-compose.yml');
  final _descController = TextEditingController();

  String? _selectedEnvId;
  final DockerComposeController _composeController = Get.find<DockerComposeController>();
  final EnvironmentController _envController = Get.find<EnvironmentController>();

  @override
  void initState() {
    super.initState();
    if (_envController.environments.isNotEmpty) {
      _selectedEnvId = _envController.environments.first.id;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _projectController.dispose();
    _dirController.dispose();
    _fileController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _onNameChanged(String val) {
    if (_projectController.text.isEmpty || _projectController.text == _slugify(_nameController.text.substring(0, _nameController.text.length > 1 ? _nameController.text.length - 1 : 0))) {
      _projectController.text = _slugify(val);
    }
  }

  String _slugify(String text) {
    return text
        .toLowerCase()
        .trim()
        .replaceAll(RegExp(r'[^a-z0-9_-]+'), '-')
        .replaceAll(RegExp(r'-+'), '-');
  }

  void _submit() {
    if (_selectedEnvId == null || _selectedEnvId!.isEmpty) {
      Get.snackbar('Validasi Gagal', 'Silakan pilih environment target.');
      return;
    }

    if (_formKey.currentState?.validate() ?? false) {
      _composeController.createProject(
        name: _nameController.text.trim(),
        projectName: _projectController.text.trim(),
        environmentId: _selectedEnvId!,
        workingDirectory: _dirController.text.trim(),
        composeFile: _fileController.text.trim(),
        description: _descController.text.trim().isEmpty ? null : _descController.text.trim(),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final envs = _envController.environments;

    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: const Color(0xFFBC8CFF).withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.add_to_photos_rounded, color: Color(0xFFBC8CFF), size: 20),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    'Registrasi Docker Compose',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Divider(color: Color(0xFF21262D), height: 1),
              const SizedBox(height: 16),

              // Environment dropdown
              const Text('Environment Target', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white70)),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: const Color(0xFF161B22),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF30363D)),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _selectedEnvId,
                    dropdownColor: const Color(0xFF161B22),
                    isExpanded: true,
                    items: envs.map((e) {
                      return DropdownMenuItem<String>(
                        value: e.id,
                        child: Text(e.name, style: const TextStyle(color: Colors.white, fontSize: 13)),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _selectedEnvId = val);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 14),

              AppTextField(
                label: 'Nama Tampilan Project',
                hint: 'Contoh: PTBI Web Application',
                controller: _nameController,
                onChanged: _onNameChanged,
                validator: (val) => (val == null || val.trim().isEmpty) ? 'Nama project wajib diisi' : null,
              ),
              const SizedBox(height: 14),

              AppTextField(
                label: 'Project Name (Identifier)',
                hint: 'Contoh: ptbi',
                controller: _projectController,
                validator: (val) {
                  if (val == null || val.trim().isEmpty) return 'Project identifier wajib diisi';
                  if (!RegExp(r'^[a-z0-9_-]+$').hasMatch(val.trim())) {
                    return 'Hanya huruf kecil, angka, _, dan -';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 14),

              AppTextField(
                label: 'Working Directory (Absolute Path)',
                hint: 'Contoh: /opt/apps/ptbi',
                controller: _dirController,
                validator: (val) {
                  if (val == null || val.trim().isEmpty) return 'Working directory wajib diisi';
                  if (!val.trim().startsWith('/')) return 'Harus absolute path diawali /';
                  return null;
                },
              ),
              const SizedBox(height: 14),

              AppTextField(
                label: 'Compose File Name',
                hint: 'docker-compose.yml',
                controller: _fileController,
                validator: (val) => (val == null || val.trim().isEmpty) ? 'Nama compose file wajib diisi' : null,
              ),
              const SizedBox(height: 14),

              AppTextField(
                label: 'Deskripsi (Opsional)',
                hint: 'Keterangan cluster compose...',
                controller: _descController,
                maxLines: 2,
              ),
              const SizedBox(height: 20),

              Obx(
                () => AppButton(
                  text: 'Simpan & Registrasi',
                  isLoading: _composeController.isLoading.value,
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
