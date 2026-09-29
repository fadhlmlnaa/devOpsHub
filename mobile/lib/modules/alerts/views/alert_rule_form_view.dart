import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../data/models/alert_model.dart';
import '../controllers/alert_rule_controller.dart';

class AlertRuleFormView extends StatefulWidget {
  final String workspaceId;
  final String? serverId;
  final String? environmentId;
  final AlertRuleModel? rule;

  const AlertRuleFormView({
    super.key,
    required this.workspaceId,
    this.serverId,
    this.environmentId,
    this.rule,
  });

  @override
  State<AlertRuleFormView> createState() => _AlertRuleFormViewState();
}

class _AlertRuleFormViewState extends State<AlertRuleFormView> {
  final _formKey = GlobalKey<FormState>();

  late TextEditingController nameCtrl;
  late TextEditingController descCtrl;
  late TextEditingController thresholdCtrl;
  late TextEditingController durationCtrl;
  late TextEditingController targetIdentifierCtrl;

  late String selectedMetricType;
  late String selectedOperator;
  late String selectedSeverity;
  late bool isEnabled;

  final List<Map<String, String>> metricTypes = [
    {'value': 'CPU_USAGE', 'label': 'Penggunaan CPU (CPU Usage)'},
    {'value': 'MEMORY_USAGE', 'label': 'Penggunaan Memori (Memory Usage)'},
    {'value': 'DISK_USAGE', 'label': 'Penggunaan Disk (Disk Usage)'},
    {'value': 'LOAD_AVERAGE', 'label': 'Beban Sistem (Load Average)'},
    {'value': 'SERVER_STATUS', 'label': 'Status Server (Offline/Online)'},
    {'value': 'SERVICE_STATUS', 'label': 'Status Layanan Systemd (Service)'},
    {'value': 'DEPLOYMENT_STATUS', 'label': 'Status Eksekusi Deployment'},
    {'value': 'BACKUP_STATUS', 'label': 'Status Operasi Backup'},
  ];

  final List<Map<String, String>> operators = [
    {'value': 'GREATER_THAN', 'label': '> (Lebih besar dari)'},
    {'value': 'GREATER_THAN_OR_EQUAL', 'label': '>= (Lebih besar atau sama)'},
    {'value': 'LESS_THAN', 'label': '< (Lebih kecil dari)'},
    {'value': 'LESS_THAN_OR_EQUAL', 'label': '<= (Lebih kecil atau sama)'},
    {'value': 'EQUAL', 'label': '== (Sama dengan)'},
    {'value': 'NOT_EQUAL', 'label': '!= (Tidak sama dengan)'},
  ];

  @override
  void initState() {
    super.initState();
    final r = widget.rule;
    nameCtrl = TextEditingController(text: r?.name ?? '');
    descCtrl = TextEditingController(text: r?.description ?? '');
    thresholdCtrl = TextEditingController(text: r != null ? '${r.threshold}' : '85.0');
    durationCtrl = TextEditingController(text: r != null ? '${r.durationSeconds}' : '60');
    targetIdentifierCtrl = TextEditingController(text: r?.targetIdentifier ?? '');

    selectedMetricType = r?.metricType ?? 'CPU_USAGE';
    selectedOperator = r?.operator ?? 'GREATER_THAN';
    selectedSeverity = r?.severity ?? 'WARNING';
    isEnabled = r?.isEnabled ?? true;
  }

  @override
  void dispose() {
    nameCtrl.dispose();
    descCtrl.dispose();
    thresholdCtrl.dispose();
    durationCtrl.dispose();
    targetIdentifierCtrl.dispose();
    super.dispose();
  }

  void _onMetricChanged(String? newMetric) {
    if (newMetric == null) return;
    setState(() {
      selectedMetricType = newMetric;
      if (newMetric == 'SERVER_STATUS' || newMetric == 'SERVICE_STATUS' || newMetric == 'DEPLOYMENT_STATUS' || newMetric == 'BACKUP_STATUS') {
        selectedOperator = 'EQUAL';
        thresholdCtrl.text = '0.0'; // 0.0 = OFFLINE/FAILED
      } else if (newMetric.contains('USAGE')) {
        selectedOperator = 'GREATER_THAN';
        thresholdCtrl.text = '90.0';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final ruleCtrl = Get.find<AlertRuleController>();
    final isEditing = widget.rule != null;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(
          isEditing ? 'Edit Aturan Alert' : 'Tambah Aturan Alert',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        backgroundColor: AppColors.surface,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Name Field
              _buildLabel('Nama Aturan Alert *'),
              TextFormField(
                controller: nameCtrl,
                style: const TextStyle(color: AppColors.textPrimary),
                decoration: _inputDecoration('Contoh: High CPU Production > 90%'),
                validator: (val) {
                  if (val == null || val.trim().isEmpty) {
                    return 'Nama aturan wajib diisi';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // Description Field
              _buildLabel('Deskripsi (Opsional)'),
              TextFormField(
                controller: descCtrl,
                style: const TextStyle(color: AppColors.textPrimary),
                maxLines: 2,
                decoration: _inputDecoration('Penjelasan kondisi pemicu dan tindakan...'),
              ),
              const SizedBox(height: 16),

              // Metric Type Dropdown
              _buildLabel('Tipe Metrik *'),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: AppColors.surfaceCard,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.border),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: selectedMetricType,
                    isExpanded: true,
                    dropdownColor: AppColors.surfaceElevated,
                    items: metricTypes.map((m) {
                      return DropdownMenuItem<String>(
                        value: m['value'],
                        child: Text(m['label']!, style: const TextStyle(color: AppColors.textPrimary, fontSize: 14)),
                      );
                    }).toList(),
                    onChanged: _onMetricChanged,
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Target Identifier (for SERVICE_STATUS)
              if (selectedMetricType == 'SERVICE_STATUS') ...[
                _buildLabel('Nama Service Systemd *'),
                TextFormField(
                  controller: targetIdentifierCtrl,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: _inputDecoration('Contoh: nginx, docker, redis-server'),
                  validator: (val) {
                    if (selectedMetricType == 'SERVICE_STATUS' && (val == null || val.trim().isEmpty)) {
                      return 'Nama service wajib diisi';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
              ],

              // Operator & Threshold
              Row(
                children: [
                  Expanded(
                    flex: 3,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildLabel('Operator *'),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          decoration: BoxDecoration(
                            color: AppColors.surfaceCard,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppColors.border),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              value: selectedOperator,
                              isExpanded: true,
                              dropdownColor: AppColors.surfaceElevated,
                              items: operators.map((o) {
                                return DropdownMenuItem<String>(
                                  value: o['value'],
                                  child: Text(o['label']!, style: const TextStyle(color: AppColors.textPrimary, fontSize: 13)),
                                );
                              }).toList(),
                              onChanged: (val) {
                                if (val != null) setState(() => selectedOperator = val);
                              },
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildLabel('Batas (Threshold) *'),
                        TextFormField(
                          controller: thresholdCtrl,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          style: const TextStyle(color: AppColors.textPrimary),
                          decoration: _inputDecoration('85.0'),
                          validator: (val) {
                            if (val == null || val.trim().isEmpty) return 'Wajib diisi';
                            final parsed = double.tryParse(val);
                            if (parsed == null) return 'Harus angka';
                            if (selectedMetricType.contains('USAGE') && (parsed < 0 || parsed > 100)) {
                              return '0 - 100%';
                            }
                            return null;
                          },
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Duration Seconds
              _buildLabel('Durasi Bertahan (Detik) *'),
              TextFormField(
                controller: durationCtrl,
                keyboardType: TextInputType.number,
                style: const TextStyle(color: AppColors.textPrimary),
                decoration: _inputDecoration('Contoh: 60 (1 menit), 300 (5 menit)'),
                validator: (val) {
                  if (val == null || val.trim().isEmpty) return 'Wajib diisi';
                  final parsed = int.tryParse(val);
                  if (parsed == null || parsed < 0) return 'Harus angka >= 0';
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // Severity Selector
              _buildLabel('Tingkat Keparahan (Severity) *'),
              Row(
                children: [
                  _buildSeverityOption('INFO', 'Info', AppColors.info),
                  const SizedBox(width: 8),
                  _buildSeverityOption('WARNING', 'Warning', AppColors.warning),
                  const SizedBox(width: 8),
                  _buildSeverityOption('CRITICAL', 'Critical', AppColors.error),
                ],
              ),
              const SizedBox(height: 16),

              // Is Enabled Switch
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.surfaceCard,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.border),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Aktifkan Aturan Ini',
                      style: TextStyle(color: AppColors.textPrimary, fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                    Switch(
                      value: isEnabled,
                      activeThumbColor: AppColors.primary,
                      onChanged: (val) => setState(() => isEnabled = val),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // Submit Button
              Obx(() => SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: AppColors.textOnPrimary,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: ruleCtrl.isSubmitting.value ? null : _submitForm,
                      child: ruleCtrl.isSubmitting.value
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.textOnPrimary),
                            )
                          : Text(
                              isEditing ? 'Simpan Perubahan' : 'Buat Aturan Alert',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                            ),
                    ),
                  )),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: const TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600),
      ),
    );
  }

  InputDecoration _inputDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: AppColors.textMuted, fontSize: 13),
      filled: true,
      fillColor: AppColors.surfaceCard,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.primary, width: 1.5)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    );
  }

  Widget _buildSeverityOption(String value, String label, Color color) {
    final isSelected = selectedSeverity == value;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => selectedSeverity = value),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected ? color.withValues(alpha: 0.2) : AppColors.surfaceCard,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isSelected ? color : AppColors.border,
              width: isSelected ? 1.5 : 1,
            ),
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                color: isSelected ? color : AppColors.textMuted,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                fontSize: 13,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;

    final ruleCtrl = Get.find<AlertRuleController>();
    final payload = {
      'name': nameCtrl.text.trim(),
      'description': descCtrl.text.trim().isEmpty ? null : descCtrl.text.trim(),
      'metric_type': selectedMetricType,
      'operator': selectedOperator,
      'threshold': double.parse(thresholdCtrl.text.trim()),
      'duration_seconds': int.parse(durationCtrl.text.trim()),
      'severity': selectedSeverity,
      'target_identifier': selectedMetricType == 'SERVICE_STATUS' ? targetIdentifierCtrl.text.trim() : null,
      'is_enabled': isEnabled,
      'server_id': widget.serverId ?? widget.rule?.serverId,
      'environment_id': widget.environmentId ?? widget.rule?.environmentId,
    };

    bool success;
    if (widget.rule != null) {
      success = await ruleCtrl.updateRule(widget.rule!.id, payload);
    } else {
      success = await ruleCtrl.createRule(payload);
    }

    if (success && mounted) {
      Navigator.of(context).pop(true);
    }
  }
}
