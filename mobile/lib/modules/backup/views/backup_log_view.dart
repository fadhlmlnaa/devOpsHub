import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import '../../../data/models/backup_model.dart';
import '../controllers/backup_controller.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../../../core/utils/formatters.dart';

class BackupLogView extends StatefulWidget {
  final String workspaceId;
  final BackupModel backup;

  const BackupLogView({
    super.key,
    required this.workspaceId,
    required this.backup,
  });

  @override
  State<BackupLogView> createState() => _BackupLogViewState();
}

class _BackupLogViewState extends State<BackupLogView> {
  late final BackupController _controller;
  final TextEditingController _searchCtrl = TextEditingController();
  String _searchQuery = '';
  final ScrollController _scrollController = ScrollController();
  Timer? _pollingTimer;

  @override
  void initState() {
    super.initState();
    _controller = Get.isRegistered<BackupController>()
        ? Get.find<BackupController>()
        : Get.put(BackupController());

    _controller.workspaceId = widget.workspaceId;
    _controller.fetchLogs(widget.backup.id);

    // Auto-polling while backup is running or pending
    _pollingTimer = Timer.periodic(const Duration(seconds: 2), (_) {
      final currentStatus = _controller.currentLogs.value?.status ?? widget.backup.status;
      if (currentStatus == 'RUNNING' || currentStatus == 'PENDING') {
        _controller.fetchLogs(widget.backup.id);
      } else {
        _pollingTimer?.cancel();
      }
    });
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _searchCtrl.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _copyAllLogs(List<BackupLogEntryModel> entries) {
    final buffer = StringBuffer();
    for (final e in entries) {
      final ts = e.timestamp != null ? AppFormatters.formatTime(e.timestamp!) : '--:--';
      buffer.writeln('[$ts] [${e.level}] ${e.message}');
    }
    Clipboard.setData(ClipboardData(text: buffer.toString()));
    Get.snackbar(
      'Disalin',
      'Seluruh log backup berhasil disalin ke clipboard.',
      backgroundColor: AppColors.success.withValues(alpha: 0.9),
      colorText: Colors.white,
      snackPosition: SnackPosition.BOTTOM,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppAppBar(
        title: 'Log Backup #${widget.backup.id.substring(0, 8)}',
        actions: [
          IconButton(
            icon: const Icon(Icons.copy_all_rounded, color: Colors.white),
            tooltip: 'Salin Semua Log',
            onPressed: () {
              final entries = _controller.currentLogs.value?.entries ?? [];
              if (entries.isNotEmpty) {
                _copyAllLogs(entries);
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Colors.white),
            tooltip: 'Muat Ulang',
            onPressed: () => _controller.fetchLogs(widget.backup.id),
          ),
        ],
      ),
      body: Column(
        children: [
          // Header Card with reactive status
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: AppColors.surfaceCard,
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.backup.backupConfigName ?? 'Backup',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${widget.backup.backupType} • ${widget.backup.environmentName ?? 'Env'} • ${widget.backup.serverName ?? 'Server'}',
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
                Obx(() {
                  final activeStatus = _controller.currentLogs.value?.status ?? widget.backup.status;
                  return _buildStatusBadge(activeStatus);
                }),
              ],
            ),
          ),

          // Search Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              controller: _searchCtrl,
              onChanged: (val) => setState(() => _searchQuery = val.toLowerCase()),
              style: const TextStyle(fontSize: 13, color: Colors.white),
              decoration: InputDecoration(
                hintText: 'Cari dalam log...',
                hintStyle: const TextStyle(color: AppColors.textSecondary, fontSize: 13),
                prefixIcon: const Icon(Icons.search_rounded, color: AppColors.textSecondary, size: 20),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear_rounded, size: 18, color: AppColors.textSecondary),
                        onPressed: () {
                          _searchCtrl.clear();
                          setState(() => _searchQuery = '');
                        },
                      )
                    : null,
                filled: true,
                fillColor: AppColors.surfaceCard,
                contentPadding: const EdgeInsets.symmetric(vertical: 8),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
              ),
            ),
          ),

          // Log entries terminal view
          Expanded(
            child: Obx(() {
              if (_controller.isLoadingLogs.value && _controller.currentLogs.value == null) {
                return const Center(child: CircularProgressIndicator(color: AppColors.primary));
              }

              final logsModel = _controller.currentLogs.value;
              final currentStatus = logsModel?.status ?? widget.backup.status;

              if (logsModel == null || logsModel.entries.isEmpty) {
                if (currentStatus == 'RUNNING' || currentStatus == 'PENDING') {
                  return const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(color: AppColors.primary),
                          SizedBox(height: 16),
                          Text(
                            'Menghubungkan & mengeksekusi backup di server...',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                return const Center(
                  child: Text(
                    'Tidak ada baris log untuk backup ini.',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                );
              }

              final filtered = _searchQuery.isEmpty
                  ? logsModel.entries
                  : logsModel.entries
                      .where((e) => e.message.toLowerCase().contains(_searchQuery))
                      .toList();

              if (filtered.isEmpty) {
                return const Center(
                  child: Text(
                    'Tidak ditemukan baris log yang cocok dengan pencarian.',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                );
              }

              return Container(
                margin: const EdgeInsets.all(12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.85),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: ListView.builder(
                  controller: _scrollController,
                  itemCount: filtered.length,
                  itemBuilder: (context, index) {
                    final item = filtered[index];
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.timestamp != null
                                ? AppFormatters.formatTime(item.timestamp!)
                                : '--:--',
                            style: TextStyle(
                              fontSize: 11,
                              fontFamily: 'monospace',
                              color: Colors.white.withValues(alpha: 0.4),
                            ),
                          ),
                          const SizedBox(width: 8),
                          _buildLogLevelTag(item.level),
                          const SizedBox(width: 8),
                          Expanded(
                            child: SelectableText(
                              item.message,
                              style: TextStyle(
                                fontSize: 12,
                                fontFamily: 'monospace',
                                color: item.isError
                                    ? AppColors.error
                                    : (item.isWarning ? AppColors.warning : Colors.white.withValues(alpha: 0.9)),
                                height: 1.3,
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildLogLevelTag(String level) {
    Color color;
    switch (level.toUpperCase()) {
      case 'ERROR':
        color = AppColors.error;
        break;
      case 'WARNING':
        color = AppColors.warning;
        break;
      default:
        color = AppColors.primary;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        level.toUpperCase(),
        style: TextStyle(
          fontSize: 9,
          fontFamily: 'monospace',
          fontWeight: FontWeight.bold,
          color: color,
        ),
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color bg;
    Color fg;
    switch (status.toUpperCase()) {
      case 'SUCCESS':
        bg = AppColors.success.withValues(alpha: 0.2);
        fg = AppColors.success;
        break;
      case 'FAILED':
        bg = AppColors.error.withValues(alpha: 0.2);
        fg = AppColors.error;
        break;
      case 'RUNNING':
        bg = AppColors.primary.withValues(alpha: 0.2);
        fg = AppColors.primary;
        break;
      default:
        bg = AppColors.warning.withValues(alpha: 0.2);
        fg = AppColors.warning;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8)),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(color: fg, fontSize: 11, fontWeight: FontWeight.bold),
      ),
    );
  }
}
