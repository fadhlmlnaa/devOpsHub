import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_text_field.dart';
import '../../environment/controllers/environment_controller.dart';
import '../controllers/server_controller.dart';

class AddServerView extends StatefulWidget {
  const AddServerView({super.key});

  @override
  State<AddServerView> createState() => _AddServerViewState();
}

class _AddServerViewState extends State<AddServerView> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _hostnameController = TextEditingController();
  final _ipController = TextEditingController();
  final _portController = TextEditingController(text: '22');
  final _usernameController = TextEditingController(text: 'ubuntu');
  final _osController = TextEditingController(text: 'Ubuntu 24.04');
  final _descController = TextEditingController();

  // Credentials
  String _authType = 'PASSWORD'; // 'PASSWORD' or 'PRIVATE_KEY'
  final _passwordController = TextEditingController();
  final _privateKeyController = TextEditingController();
  final _passphraseController = TextEditingController();
  bool _obscurePassword = true;

  String? _selectedEnvironmentId;

  final ServerController _serverController = Get.find<ServerController>();
  final EnvironmentController _envController = Get.find<EnvironmentController>();

  late final String _workspaceId;

  @override
  void initState() {
    super.initState();
    _workspaceId = Get.parameters['id'] ?? '';
    if (_envController.environments.isNotEmpty) {
      _selectedEnvironmentId = _envController.environments.first.id;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _hostnameController.dispose();
    _ipController.dispose();
    _portController.dispose();
    _usernameController.dispose();
    _osController.dispose();
    _descController.dispose();
    _passwordController.dispose();
    _privateKeyController.dispose();
    _passphraseController.dispose();
    super.dispose();
  }

  void _submit() async {
    if (_formKey.currentState?.validate() ?? false) {
      if (_selectedEnvironmentId == null || _selectedEnvironmentId!.isEmpty) {
        Get.snackbar(
          'Pilih Environment',
          'Silakan pilih environment terlebih dahulu.',
          snackPosition: SnackPosition.BOTTOM,
        );
        return;
      }

      final success = await _serverController.createServer(
        workspaceId: _workspaceId,
        environmentId: _selectedEnvironmentId!,
        name: _nameController.text.trim(),
        hostname: _hostnameController.text.trim().isEmpty ? null : _hostnameController.text.trim(),
        ipAddress: _ipController.text.trim().isEmpty ? null : _ipController.text.trim(),
        sshPort: int.tryParse(_portController.text.trim()) ?? 22,
        username: _usernameController.text.trim().isEmpty ? null : _usernameController.text.trim(),
        operatingSystem: _osController.text.trim().isEmpty ? null : _osController.text.trim(),
        description: _descController.text.trim().isEmpty ? null : _descController.text.trim(),
        authType: _authType,
        password: _authType == 'PASSWORD' && _passwordController.text.isNotEmpty ? _passwordController.text : null,
        privateKey: _authType == 'PRIVATE_KEY' && _privateKeyController.text.isNotEmpty ? _privateKeyController.text : null,
        passphrase: _authType == 'PRIVATE_KEY' && _passphraseController.text.isNotEmpty ? _passphraseController.text : null,
      );

      if (success && mounted) {
        Navigator.of(context).pop();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const AppAppBar(
        title: 'Tambah Server Baru',
        subtitle: 'Konfigurasi server dan kredensial SSH terenkripsi',
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Environment Selector
                const Text(
                  'Pilih Environment',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textSecondary),
                ),
                const SizedBox(height: 6),
                Obx(() {
                  final envs = _envController.environments;
                  if (envs.isEmpty) {
                    return Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceElevated,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: const Text('Belum ada environment. Buat environment terlebih dahulu.'),
                    );
                  }

                  if (_selectedEnvironmentId == null && envs.isNotEmpty) {
                    _selectedEnvironmentId = envs.first.id;
                  }

                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceElevated,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: _selectedEnvironmentId,
                        isExpanded: true,
                        dropdownColor: AppColors.surfaceElevated,
                        icon: const Icon(Icons.arrow_drop_down_rounded, color: AppColors.textSecondary),
                        items: envs.map((e) {
                          return DropdownMenuItem<String>(
                            value: e.id,
                            child: Row(
                              children: [
                                const Icon(Icons.layers_rounded, size: 18, color: AppColors.primary),
                                const SizedBox(width: 10),
                                Text(e.name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                              ],
                            ),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() {
                              _selectedEnvironmentId = val;
                            });
                          }
                        },
                      ),
                    ),
                  );
                }),

                const SizedBox(height: 16),
                AppTextField(
                  label: 'Nama Server',
                  hint: 'e.g. Production App Server',
                  controller: _nameController,
                  prefixIcon: const Icon(Icons.dns_rounded, size: 20),
                  validator: (val) => (val == null || val.trim().isEmpty) ? 'Nama server wajib diisi' : null,
                ),

                const SizedBox(height: 16),
                AppTextField(
                  label: 'IP Address',
                  hint: 'e.g. 103.120.45.67 atau 192.168.1.8',
                  controller: _ipController,
                  prefixIcon: const Icon(Icons.language_rounded, size: 20),
                  validator: (val) {
                    final ip = val?.trim() ?? '';
                    final host = _hostnameController.text.trim();
                    if (ip.isEmpty && host.isEmpty) {
                      return 'IP Address atau Hostname wajib diisi';
                    }
                    return null;
                  },
                ),

                const SizedBox(height: 16),
                AppTextField(
                  label: 'Hostname / FQDN (Opsional)',
                  hint: 'e.g. host.docker.internal / app-01.prod.lan',
                  controller: _hostnameController,
                  prefixIcon: const Icon(Icons.alternate_email_rounded, size: 20),
                ),

                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      flex: 1,
                      child: AppTextField(
                        label: 'Port SSH',
                        hint: '22',
                        controller: _portController,
                        keyboardType: TextInputType.number,
                        prefixIcon: const Icon(Icons.tag_rounded, size: 20),
                        validator: (val) => (val == null || int.tryParse(val.trim()) == null) ? 'Port harus angka' : null,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      flex: 2,
                      child: AppTextField(
                        label: 'SSH Username',
                        hint: 'ubuntu / root / user',
                        controller: _usernameController,
                        prefixIcon: const Icon(Icons.person_outline_rounded, size: 20),
                        validator: (val) => (val == null || val.trim().isEmpty) ? 'Username wajib diisi' : null,
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: AppTextField(
                        label: 'Operating System',
                        hint: 'Ubuntu 24.04 LTS',
                        controller: _osController,
                        prefixIcon: const Icon(Icons.memory_rounded, size: 20),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: AppTextField(
                        label: 'Deskripsi (Opsional)',
                        hint: 'e.g. Server utama backend',
                        controller: _descController,
                        prefixIcon: const Icon(Icons.notes_rounded, size: 20),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 24),
                const Divider(color: AppColors.border, height: 1),
                const SizedBox(height: 16),

                // Credentials Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Kredensial SSH (Terenkripsi)',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                    ),
                    Container(
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Row(
                        children: [
                          _buildAuthTab('PASSWORD', 'Password'),
                          _buildAuthTab('PRIVATE_KEY', 'Private Key'),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                if (_authType == 'PASSWORD') ...[
                  AppTextField(
                    label: 'SSH Password',
                    hint: '••••••••••••',
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
                    suffixIcon: IconButton(
                      icon: Icon(_obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 20),
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                ] else ...[
                  AppTextField(
                    label: 'OpenSSH Private Key',
                    hint: '-----BEGIN OPENSSH PRIVATE KEY-----\n...',
                    controller: _privateKeyController,
                    maxLines: 4,
                    prefixIcon: const Icon(Icons.vpn_key_rounded, size: 20),
                  ),
                  const SizedBox(height: 12),
                  AppTextField(
                    label: 'Passphrase (Opsional)',
                    hint: 'Jika private key dienkripsi',
                    controller: _passphraseController,
                    obscureText: true,
                    prefixIcon: const Icon(Icons.lock_clock_outlined, size: 20),
                  ),
                ],

                const SizedBox(height: 28),
                Obx(
                  () => AppButton(
                    text: 'Simpan Server',
                    isLoading: _serverController.isCreating.value,
                    icon: const Icon(Icons.save_rounded, size: 20),
                    onPressed: _submit,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildAuthTab(String type, String label) {
    final isSelected = _authType == type;
    return GestureDetector(
      onTap: () => setState(() => _authType = type),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: isSelected ? AppColors.textOnPrimary : AppColors.textSecondary,
          ),
        ),
      ),
    );
  }
}
