import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/log_model.dart';
import '../../../data/services/docker_service.dart';
import '../../log/widgets/log_entry_widget.dart';
import '../../log/widgets/log_filter_widget.dart';

class ContainerLogView extends StatefulWidget {
  final String workspaceId;
  final String serverId;
  final String serverName;
  final String containerId;
  final String containerName;

  const ContainerLogView({
    super.key,
    required this.workspaceId,
    required this.serverId,
    required this.serverName,
    required this.containerId,
    required this.containerName,
  });

  @override
  State<ContainerLogView> createState() => _ContainerLogViewState();
}

class _ContainerLogViewState extends State<ContainerLogView> {
  final DockerService _dockerService = Get.find<DockerService>();
  final ScrollController _scrollController = ScrollController();

  final RxBool isLoading = false.obs;
  final RxString errorMessage = ''.obs;
  final RxList<LogEntryModel> entries = <LogEntryModel>[].obs;
  final RxBool isTruncated = false.obs;

  final RxInt selectedLines = 100.obs;
  final RxnString selectedSince = RxnString();
  final RxString searchQuery = ''.obs;

  final RxBool showLineNumbers = true.obs;
  final RxBool showTimestamps = true.obs;
  bool _showFilters = true;

  @override
  void initState() {
    super.initState();
    _loadLogs();
  }

  List<LogEntryModel> get filteredEntries {
    final list = entries.toList();
    final q = searchQuery.value.trim().toLowerCase();
    if (q.isEmpty) return list;
    return list.where((e) => e.message.toLowerCase().contains(q)).toList();
  }

  Future<void> _loadLogs({bool silent = false}) async {
    if (!silent) {
      isLoading.value = true;
      errorMessage.value = '';
    }

    try {
      final res = await _dockerService.getContainerLogs(
        widget.workspaceId,
        widget.serverId,
        widget.containerId,
        lines: selectedLines.value,
        since: selectedSince.value,
      );

      entries.assignAll(res.entries);
      isTruncated.value = res.truncated;
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Terjadi kesalahan saat memuat log container.';
    } finally {
      if (!silent) isLoading.value = false;
    }
  }

  void _copyAll() {
    final list = filteredEntries;
    if (list.isEmpty) return;
    final text = list.map((e) => e.message).join('\n');
    Clipboard.setData(ClipboardData(text: text));
    Get.snackbar(
      'Tersalin',
      '${list.length} baris log berhasil disalin ke clipboard.',
      snackPosition: SnackPosition.BOTTOM,
      backgroundColor: const Color(0xFF161B22),
      colorText: const Color(0xFF7EE787),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF090D12),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18, color: Color(0xFFE6EDF3)),
          onPressed: () => Get.back(),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.terminal_rounded, size: 16, color: Color(0xFF58A6FF)),
                const SizedBox(width: 6),
                Text(
                  widget.containerName,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white, fontFamily: 'monospace'),
                ),
              ],
            ),
            Text(
              'Container: ${widget.containerId} | ${widget.serverName}',
              style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF8B949E)),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(_showFilters ? Icons.tune_rounded : Icons.tune_outlined, color: _showFilters ? const Color(0xFF58A6FF) : const Color(0xFF8B949E), size: 20),
            tooltip: 'Filter',
            onPressed: () => setState(() => _showFilters = !_showFilters),
          ),
          IconButton(
            icon: const Icon(Icons.copy_all_rounded, color: Color(0xFF8B949E), size: 20),
            tooltip: 'Salin Seluruh Log',
            onPressed: _copyAll,
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF7EE787), size: 20),
            tooltip: 'Refresh Log',
            onPressed: () => _loadLogs(),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (_showFilters) ...[
              Obx(
                () => LogFilterWidget(
                  selectedLines: selectedLines.value,
                  selectedSince: selectedSince.value,
                  onLinesChanged: (lines) {
                    selectedLines.value = lines;
                    _loadLogs();
                  },
                  onSinceChanged: (since) {
                    selectedSince.value = since;
                    _loadLogs();
                  },
                ),
              ),
              // Search Grep Bar
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                color: const Color(0xFF161B22),
                child: Row(
                  children: [
                    Expanded(
                      child: Container(
                        height: 36,
                        decoration: BoxDecoration(
                          color: const Color(0xFF0D1117),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: const Color(0xFF30363D)),
                        ),
                        child: TextField(
                          style: const TextStyle(color: Color(0xFFE6EDF3), fontSize: 12, fontFamily: 'monospace'),
                          decoration: const InputDecoration(
                            hintText: 'grep -i "keyword"...',
                            hintStyle: TextStyle(color: Color(0xFF484F58), fontSize: 12, fontFamily: 'monospace'),
                            prefixIcon: Icon(Icons.search_rounded, color: Color(0xFF58A6FF), size: 16),
                            contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            border: InputBorder.none,
                          ),
                          onChanged: (val) => searchQuery.value = val,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Obx(() {
                      final count = filteredEntries.length;
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFF21262D),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '$count lines',
                          style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF8B949E)),
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ],

            // Terminal Title Bar (macOS Style)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: const BoxDecoration(
                color: Color(0xFF161B22),
                border: Border(
                  top: BorderSide(color: Color(0xFF21262D), width: 1),
                  bottom: BorderSide(color: Color(0xFF21262D), width: 1),
                ),
              ),
              child: Row(
                children: [
                  Container(width: 10, height: 10, decoration: const BoxDecoration(color: Color(0xFFFF5F56), shape: BoxShape.circle)),
                  const SizedBox(width: 6),
                  Container(width: 10, height: 10, decoration: const BoxDecoration(color: Color(0xFFFFBD2E), shape: BoxShape.circle)),
                  const SizedBox(width: 6),
                  Container(width: 10, height: 10, decoration: const BoxDecoration(color: Color(0xFF27C93F), shape: BoxShape.circle)),
                  const SizedBox(width: 12),
                  Obx(
                    () => Expanded(
                      child: Text(
                        'docker logs --tail ${selectedLines.value} ${widget.containerName}',
                        style: const TextStyle(fontFamily: 'monospace', fontSize: 11, color: Color(0xFF8B949E)),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                  Obx(
                    () => Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        InkWell(
                          onTap: () => showLineNumbers.toggle(),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: Text(
                              '#NUM',
                              style: TextStyle(
                                fontSize: 10,
                                fontFamily: 'monospace',
                                fontWeight: FontWeight.bold,
                                color: showLineNumbers.value ? const Color(0xFF58A6FF) : const Color(0xFF484F58),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        InkWell(
                          onTap: () => showTimestamps.toggle(),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: Text(
                              'TIME',
                              style: TextStyle(
                                fontSize: 10,
                                fontFamily: 'monospace',
                                fontWeight: FontWeight.bold,
                                color: showTimestamps.value ? const Color(0xFF58A6FF) : const Color(0xFF484F58),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Truncated Warning Banner
            Obx(() {
              if (isTruncated.value) {
                return Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  color: const Color(0xFFD29922).withValues(alpha: 0.15),
                  child: const Row(
                    children: [
                      Icon(Icons.warning_amber_rounded, size: 14, color: Color(0xFFD29922)),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '[TRUNCATED] Log melebihi batas 1MB, dipotong ke baris terbaru.',
                          style: TextStyle(color: Color(0xFFE3B341), fontSize: 10, fontFamily: 'monospace'),
                        ),
                      ),
                    ],
                  ),
                );
              }
              return const SizedBox.shrink();
            }),

            // Terminal Output Console
            Expanded(
              child: Container(
                color: const Color(0xFF0D1117),
                child: Obx(() {
                  if (isLoading.value) {
                    return const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(Color(0xFF58A6FF))),
                          SizedBox(height: 12),
                          Text('Executing docker logs...', style: TextStyle(fontFamily: 'monospace', color: Color(0xFF8B949E), fontSize: 12)),
                        ],
                      ),
                    );
                  }

                  if (errorMessage.value.isNotEmpty && entries.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.error_outline_rounded, size: 40, color: Color(0xFFFF7B72)),
                            const SizedBox(height: 12),
                            Text(errorMessage.value, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontFamily: 'monospace', fontSize: 13)),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF238636)),
                              onPressed: () => _loadLogs(),
                              icon: const Icon(Icons.refresh_rounded, size: 16),
                              label: const Text('Coba Lagi'),
                            ),
                          ],
                        ),
                      ),
                    );
                  }

                  final list = filteredEntries;
                  if (list.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.receipt_long_rounded, size: 40, color: Color(0xFF30363D)),
                          const SizedBox(height: 12),
                          const Text('Tidak ada log container ditemukan.', style: TextStyle(color: Color(0xFF8B949E), fontSize: 13, fontFamily: 'monospace')),
                          const SizedBox(height: 16),
                          TextButton.icon(
                            onPressed: () => _loadLogs(),
                            icon: const Icon(Icons.refresh_rounded, size: 16, color: Color(0xFF58A6FF)),
                            label: const Text('Muat Ulang', style: TextStyle(color: Color(0xFF58A6FF), fontFamily: 'monospace')),
                          ),
                        ],
                      ),
                    );
                  }

                  return RefreshIndicator(
                    color: const Color(0xFF58A6FF),
                    backgroundColor: const Color(0xFF161B22),
                    onRefresh: () => _loadLogs(silent: true),
                    child: ListView.builder(
                      controller: _scrollController,
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: list.length,
                      itemBuilder: (ctx, idx) {
                        final item = list[idx];
                        return LogEntryWidget(
                          entry: item,
                          lineNumber: idx + 1,
                          showLineNumber: showLineNumbers.value,
                          showTimestamp: showTimestamps.value,
                          onCopy: () {
                            Clipboard.setData(ClipboardData(text: item.message));
                            Get.snackbar('Tersalin', 'Baris log tersalin ke clipboard.', snackPosition: SnackPosition.BOTTOM, duration: const Duration(seconds: 2));
                          },
                        );
                      },
                    ),
                  );
                }),
              ),
            ),

            // Terminal Status Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: const BoxDecoration(
                color: Color(0xFF161B22),
                border: Border(top: BorderSide(color: Color(0xFF21262D), width: 1)),
              ),
              child: Obx(() {
                final count = filteredEntries.length;
                final req = selectedLines.value;
                final since = selectedSince.value ?? 'all';

                return Row(
                  children: [
                    Container(width: 6, height: 6, decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFF58A6FF))),
                    const SizedBox(width: 8),
                    Text(
                      'STATUS: OK | LINES: $count/$req | SINCE: $since',
                      style: const TextStyle(fontFamily: 'monospace', fontSize: 10, color: Color(0xFF8B949E)),
                    ),
                    const Spacer(),
                    InkWell(
                      onTap: () {
                        if (_scrollController.hasClients) {
                          _scrollController.animateTo(0, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
                        }
                      },
                      child: const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 4),
                        child: Text('▲ TOP', style: TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF58A6FF))),
                      ),
                    ),
                    const SizedBox(width: 6),
                    InkWell(
                      onTap: () {
                        if (_scrollController.hasClients) {
                          _scrollController.animateTo(_scrollController.position.maxScrollExtent, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
                        }
                      },
                      child: const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 4),
                        child: Text('▼ BOTTOM', style: TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF58A6FF))),
                      ),
                    ),
                  ],
                );
              }),
            ),
          ],
        ),
      ),
    );
  }
}
