import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/deployment_model.dart';
import '../controllers/deployment_config_controller.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_text_field.dart';

class DeploymentConfigFormView extends StatefulWidget {
  final String workspaceId;
  final String? environmentId;
  final String? serverId;
  final DeploymentConfigModel? config;

  const DeploymentConfigFormView({
    super.key,
    required this.workspaceId,
    this.environmentId,
    this.serverId,
    this.config,
  });

  @override
  State<DeploymentConfigFormView> createState() => _DeploymentConfigFormViewState();
}

class _DeploymentConfigFormViewState extends State<DeploymentConfigFormView> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _nameCtrl;
  late final TextEditingController _appCtrl;
  late final TextEditingController _workDirCtrl;
  late final TextEditingController _branchCtrl;
  late final TextEditingController _repoUrlCtrl;
  late final TextEditingController _serviceCtrl;
  late final TextEditingController _composeCtrl;
  late final TextEditingController _descCtrl;

  String _deploymentType = 'SYSTEMD';
  String? _selectedEnvId;
  String? _selectedSrvId;

  late final DeploymentConfigController _controller;

  @override
  void initState() {
    super.initState();
    _controller = Get.find<DeploymentConfigController>();

    final cfg = widget.config;
    _nameCtrl = TextEditingController(text: cfg?.name ?? '');
    _appCtrl = TextEditingController(text: cfg?.applicationName ?? '');
    _workDirCtrl = TextEditingController(text: cfg?.workingDirectory ?? '');
    _branchCtrl = TextEditingController(text: cfg?.branch ?? 'main');
    _repoUrlCtrl = TextEditingController(text: cfg?.repositoryUrl ?? '');
    _serviceCtrl = TextEditingController(text: cfg?.restartServiceName ?? '');
    _composeCtrl = TextEditingController(text: cfg?.composeProjectName ?? '');
    _descCtrl = TextEditingController(text: cfg?.description ?? '');

    _deploymentType = cfg?.deploymentType ?? 'SYSTEMD';
    _selectedEnvId = cfg?.environmentId ?? widget.environmentId;
    _selectedSrvId = cfg?.serverId ?? widget.serverId;
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _appCtrl.dispose();
    _workDirCtrl.dispose();
    _branchCtrl.dispose();
    _repoUrlCtrl.dispose();
    _serviceCtrl.dispose();
    _composeCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedEnvId == null || _selectedSrvId == null) {
      Get.snackbar('Validasi Gagal', 'Environment dan Server wajib dipilih.');
      return;
    }

    final payload = {
      'name': _nameCtrl.text.trim(),
      'application_name': _appCtrl.text.trim(),
      'working_directory': _workDirCtrl.text.trim(),
      'deployment_type': _deploymentType,
      'branch': _branchCtrl.text.trim().isNotEmpty ? _branchCtrl.text.trim() : null,
      'repository_url': _repoUrlCtrl.text.trim().isNotEmpty ? _repoUrlCtrl.text.trim() : null,
      'restart_service_name': _deploymentType == 'SYSTEMD' && _serviceCtrl.text.trim().isNotEmpty
          ? _serviceCtrl.text.trim()
          : null,
      'compose_project_name': _deploymentType == 'DOCKER_COMPOSE' && _composeCtrl.text.trim().isNotEmpty
          ? _composeCtrl.text.trim()
          : null,
      'description': _descCtrl.text.trim().isNotEmpty ? _descCtrl.text.trim() : null,
      'environment_id': _selectedEnvId,
      'server_id': _selectedSrvId,
      'is_active': true,
    };

    bool success = false;
    if (widget.config == null) {
      success = await _controller.createConfig(payload);
    } else {
      success = await _controller.updateConfig(widget.config!.id, payload);
    }

    if (success) {
      Get.back(result: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.config != null;

    return Scaffold(
      appBar: AppAppBar(
        title: isEditing ? 'Edit Konfigurasi' : 'Daftar Konfigurasi Baru',
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Tipe Deployment Selector
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.surfaceCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Tipe Deployment Workflow',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: ChoiceChip(
                          label: const Center(child: Text('Systemd Linux')),
                          selected: _deploymentType == 'SYSTEMD',
                          selectedColor: AppColors.primary.withValues(alpha: 0.25),
                          labelStyle: TextStyle(
                            color: _deploymentType == 'SYSTEMD' ? AppColors.primary : Colors.white70,
                            fontWeight: FontWeight.bold,
                          ),
                          onSelected: (val) {
                            if (val) setState(() => _deploymentType = 'SYSTEMD');
                          },
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: ChoiceChip(
                          label: const Center(child: Text('Docker Compose')),
                          selected: _deploymentType == 'DOCKER_COMPOSE',
                          selectedColor: AppColors.primary.withValues(alpha: 0.25),
                          labelStyle: TextStyle(
                            color: _deploymentType == 'DOCKER_COMPOSE' ? AppColors.primary : Colors.white70,
                            fontWeight: FontWeight.bold,
                          ),
                          onSelected: (val) {
                            if (val) setState(() => _deploymentType = 'DOCKER_COMPOSE');
                          },
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            AppTextField(
              controller: _nameCtrl,
              label: 'Nama Konfigurasi *',
              hint: 'Misal: PTBI Odoo Staging',
              validator: (v) => v == null || v.trim().isEmpty ? 'Nama wajib diisi' : null,
            ),
            const SizedBox(height: 16),

            AppTextField(
              controller: _appCtrl,
              label: 'Nama Aplikasi *',
              hint: 'Misal: odoo, node-api, web-frontend',
              validator: (v) => v == null || v.trim().isEmpty ? 'Nama aplikasi wajib diisi' : null,
            ),
            const SizedBox(height: 16),

            AppTextField(
              controller: _workDirCtrl,
              label: 'Direktori Kerja Absolut *',
              hint: 'Misal: /opt/apps/my-app',
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Direktori kerja wajib diisi';
                if (!v.trim().startsWith('/')) return 'Wajib path absolut (diawali "/")';
                return null;
              },
            ),
            const SizedBox(height: 16),

            AppTextField(
              controller: _branchCtrl,
              label: 'Git Branch (Opsional)',
              hint: 'Misal: main, master, release/v1.0',
            ),
            const SizedBox(height: 16),

            if (_deploymentType == 'SYSTEMD') ...[
              AppTextField(
                controller: _serviceCtrl,
                label: 'Systemd Service Unit Name *',
                hint: 'Misal: myapp.service',
                validator: (v) {
                  if (_deploymentType == 'SYSTEMD' && (v == null || !v.trim().endsWith('.service'))) {
                    return 'Wajib berakhiran .service';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
            ] else ...[
              AppTextField(
                controller: _composeCtrl,
                label: 'Nama Docker Compose Project',
                hint: 'Misal: myapp_stack',
              ),
              const SizedBox(height: 16),
            ],

            AppTextField(
              controller: _descCtrl,
              label: 'Deskripsi (Opsional)',
              hint: 'Keterangan tentang konfigurasi rilis ini',
              maxLines: 2,
            ),
            const SizedBox(height: 24),

            Obx(() => AppButton(
                  text: isEditing ? 'Simpan Perubahan' : 'Daftarkan Konfigurasi',
                  isLoading: _controller.isSubmitting.value,
                  onPressed: _submit,
                )),
          ],
        ),
      ),
    );
  }
}
