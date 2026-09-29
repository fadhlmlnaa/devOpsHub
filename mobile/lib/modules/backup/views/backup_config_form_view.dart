import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/backup_model.dart';
import '../controllers/backup_config_controller.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_text_field.dart';

class BackupConfigFormView extends StatefulWidget {
  final String workspaceId;
  final String? environmentId;
  final String? serverId;
  final BackupConfigModel? config;

  const BackupConfigFormView({
    super.key,
    required this.workspaceId,
    this.environmentId,
    this.serverId,
    this.config,
  });

  @override
  State<BackupConfigFormView> createState() => _BackupConfigFormViewState();
}

class _BackupConfigFormViewState extends State<BackupConfigFormView> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _nameCtrl;
  late final TextEditingController _sourceCtrl;
  late final TextEditingController _destCtrl;
  late final TextEditingController _retentionCtrl;
  late final TextEditingController _descCtrl;

  String _backupType = 'POSTGRESQL';
  bool _isCompressed = true;
  String? _selectedEnvId;
  String? _selectedSrvId;

  late final BackupConfigController _controller;

  @override
  void initState() {
    super.initState();
    _controller = Get.find<BackupConfigController>();

    final cfg = widget.config;
    _nameCtrl = TextEditingController(text: cfg?.name ?? '');
    _sourceCtrl = TextEditingController(text: cfg?.source ?? '');
    _destCtrl = TextEditingController(text: cfg?.destination ?? '');
    _retentionCtrl = TextEditingController(text: (cfg?.retentionDays ?? 7).toString());
    _descCtrl = TextEditingController(text: cfg?.description ?? '');

    _backupType = cfg?.backupType ?? 'POSTGRESQL';
    _isCompressed = cfg?.isCompressed ?? true;
    _selectedEnvId = cfg?.environmentId ?? widget.environmentId;
    _selectedSrvId = cfg?.serverId ?? widget.serverId;
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _sourceCtrl.dispose();
    _destCtrl.dispose();
    _retentionCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  String get _sourceLabel {
    switch (_backupType) {
      case 'POSTGRESQL':
        return 'Nama Database PostgreSQL *';
      case 'FILESYSTEM':
        return 'Path Direktori Sumber Absolut *';
      case 'DOCKER_VOLUME':
        return 'Nama Docker Volume *';
      default:
        return 'Sumber Target *';
    }
  }

  String get _sourceHint {
    switch (_backupType) {
      case 'POSTGRESQL':
        return 'Misal: my_production_db';
      case 'FILESYSTEM':
        return 'Misal: /opt/myapp/uploads';
      case 'DOCKER_VOLUME':
        return 'Misal: myapp_postgres_data';
      default:
        return 'Target sumber';
    }
  }

  String get _destHint {
    switch (_backupType) {
      case 'POSTGRESQL':
        return 'Misal: /var/backups/postgresql';
      case 'FILESYSTEM':
        return 'Misal: /var/backups/filesystem';
      case 'DOCKER_VOLUME':
        return 'Misal: /var/backups/docker';
      default:
        return '/var/backups';
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedEnvId == null || _selectedSrvId == null) {
      Get.snackbar('Validasi Gagal', 'Environment dan Server wajib terhubung.');
      return;
    }

    final retention = int.tryParse(_retentionCtrl.text.trim()) ?? 7;

    final payload = {
      'name': _nameCtrl.text.trim(),
      'backup_type': _backupType,
      'source': _sourceCtrl.text.trim(),
      'destination': _destCtrl.text.trim(),
      'retention_days': retention,
      'is_compressed': _isCompressed,
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

    if (success && mounted) {
      Navigator.of(context).pop(true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.config != null;

    return Scaffold(
      appBar: AppAppBar(
        title: isEditing ? 'Edit Konfigurasi Backup' : 'Tambah Target Backup',
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Backup Type Selector Card
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
                    'Tipe Target Backup',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ChoiceChip(
                        label: const Text('PostgreSQL'),
                        selected: _backupType == 'POSTGRESQL',
                        selectedColor: const Color(0xFF336791).withValues(alpha: 0.35),
                        labelStyle: TextStyle(
                          color: _backupType == 'POSTGRESQL' ? Colors.white : Colors.white70,
                          fontWeight: FontWeight.bold,
                        ),
                        onSelected: (val) {
                          if (val) setState(() => _backupType = 'POSTGRESQL');
                        },
                      ),
                      ChoiceChip(
                        label: const Text('Filesystem'),
                        selected: _backupType == 'FILESYSTEM',
                        selectedColor: Colors.amber.withValues(alpha: 0.35),
                        labelStyle: TextStyle(
                          color: _backupType == 'FILESYSTEM' ? Colors.white : Colors.white70,
                          fontWeight: FontWeight.bold,
                        ),
                        onSelected: (val) {
                          if (val) setState(() => _backupType = 'FILESYSTEM');
                        },
                      ),
                      ChoiceChip(
                        label: const Text('Docker Volume'),
                        selected: _backupType == 'DOCKER_VOLUME',
                        selectedColor: const Color(0xFF0db7ed).withValues(alpha: 0.35),
                        labelStyle: TextStyle(
                          color: _backupType == 'DOCKER_VOLUME' ? Colors.white : Colors.white70,
                          fontWeight: FontWeight.bold,
                        ),
                        onSelected: (val) {
                          if (val) setState(() => _backupType = 'DOCKER_VOLUME');
                        },
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
              hint: 'Misal: DB Production Harian / Uploads Media',
              validator: (v) => v == null || v.trim().isEmpty ? 'Nama wajib diisi' : null,
            ),
            const SizedBox(height: 16),

            AppTextField(
              controller: _sourceCtrl,
              label: _sourceLabel,
              hint: _sourceHint,
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Sumber target wajib diisi';
                if (_backupType == 'FILESYSTEM' && !v.trim().startsWith('/')) {
                  return 'Wajib path direktori absolut (diawali "/")';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),

            AppTextField(
              controller: _destCtrl,
              label: 'Direktori Tujuan di Server *',
              hint: _destHint,
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Direktori tujuan wajib diisi';
                if (!v.trim().startsWith('/')) return 'Wajib path absolut (diawali "/")';
                return null;
              },
            ),
            const SizedBox(height: 16),

            AppTextField(
              controller: _retentionCtrl,
              label: 'Periode Retensi (Hari) *',
              hint: '7',
              keyboardType: TextInputType.number,
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Retensi hari wajib diisi';
                final n = int.tryParse(v.trim());
                if (n == null || n < 1) return 'Wajib angka positif minimal 1';
                return null;
              },
            ),
            const SizedBox(height: 16),

            // Compression Switch Tile
            Container(
              decoration: BoxDecoration(
                color: AppColors.surfaceCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: SwitchListTile(
                title: const Text(
                  'Kompresi Berkas (gzip / tar.gz)',
                  style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                ),
                subtitle: const Text(
                  'Menghemat kapasitas penyimpanan server',
                  style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
                ),
                value: _isCompressed,
                activeThumbColor: AppColors.primary,
                onChanged: (val) => setState(() => _isCompressed = val),
              ),
            ),
            const SizedBox(height: 16),

            AppTextField(
              controller: _descCtrl,
              label: 'Deskripsi (Opsional)',
              hint: 'Keterangan tentang target cadangan data ini',
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
