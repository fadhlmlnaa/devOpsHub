import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/log_model.dart';
import '../../../data/services/log_service.dart';

class LogController extends GetxController {
  final LogService logService;

  LogController({required this.logService});

  final RxBool isLoading = false.obs;
  final Rxn<LogResponseModel> logResponse = Rxn<LogResponseModel>();
  final RxList<LogEntryModel> entries = <LogEntryModel>[].obs;

  final RxInt selectedLines = 100.obs;
  final RxnString selectedSince = RxnString(); // null (all), '5m', '10m', '30m', '1h', '6h', '24h'
  final RxString searchQuery = ''.obs;
  final RxString errorMessage = ''.obs;

  final RxBool wrapLines = true.obs;
  final RxBool showLineNumbers = true.obs;
  final RxBool showTimestamps = true.obs;
  final RxBool autoScrollToBottom = false.obs;

  final ScrollController scrollController = ScrollController();

  final RxString currentWorkspaceId = ''.obs;
  final RxString currentServerId = ''.obs;
  final RxString currentServerName = ''.obs;
  final RxString currentServiceName = ''.obs;

  void toggleWrap() => wrapLines.toggle();
  void toggleLineNumbers() => showLineNumbers.toggle();
  void toggleTimestamps() => showTimestamps.toggle();
  void toggleAutoScroll() => autoScrollToBottom.toggle();

  void scrollToBottom() {
    if (scrollController.hasClients) {
      scrollController.animateTo(
        scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void scrollToTop() {
    if (scrollController.hasClients) {
      scrollController.animateTo(
        0,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void initContext({
    required String workspaceId,
    required String serverId,
    required String serviceName,
    String serverName = '',
  }) {
    currentWorkspaceId.value = workspaceId;
    currentServerId.value = serverId;
    currentServiceName.value = serviceName;
    currentServerName.value = serverName;
    searchQuery.value = '';
    loadLogs();
  }

  List<LogEntryModel> get filteredEntries {
    final list = entries.toList();
    final q = searchQuery.value.trim().toLowerCase();
    if (q.isEmpty) return list;

    return list.where((entry) {
      final msgMatch = entry.message.toLowerCase().contains(q);
      final prioMatch = entry.priority.toLowerCase().contains(q);
      return msgMatch || prioMatch;
    }).toList();
  }

  void setLines(int lines) {
    if (selectedLines.value == lines) return;
    selectedLines.value = lines;
    loadLogs();
  }

  void setSince(String? since) {
    if (selectedSince.value == since) return;
    selectedSince.value = since;
    loadLogs();
  }

  void setSearch(String query) {
    searchQuery.value = query;
  }

  Future<void> loadLogs({bool silent = false}) async {
    if (currentWorkspaceId.value.isEmpty ||
        currentServerId.value.isEmpty ||
        currentServiceName.value.isEmpty) {
      return;
    }

    if (!silent) {
      isLoading.value = true;
      errorMessage.value = '';
    }

    try {
      final res = await logService.getServiceLogs(
        currentWorkspaceId.value,
        currentServerId.value,
        currentServiceName.value,
        lines: selectedLines.value,
        since: selectedSince.value,
      );

      logResponse.value = res;
      entries.assignAll(res.entries);
      if (autoScrollToBottom.value) {
        WidgetsBinding.instance.addPostFrameCallback((_) => scrollToBottom());
      }
    } on ApiException catch (e) {
      errorMessage.value = e.message;
      if (!silent) {
        Get.snackbar(
          'Gagal Memuat Log',
          e.message,
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.red.withValues(alpha: 0.85),
          colorText: Colors.white,
        );
      }
    } catch (e) {
      errorMessage.value = 'Terjadi kesalahan saat memuat log service.';
    } finally {
      if (!silent) {
        isLoading.value = false;
      }
    }
  }

  void copyEntry(String text) {
    Clipboard.setData(ClipboardData(text: text));
    Get.snackbar(
      'Tersalin',
      'Baris log berhasil disalin ke clipboard.',
      snackPosition: SnackPosition.BOTTOM,
      backgroundColor: const Color(0xFF1E293B),
      colorText: Colors.tealAccent,
      duration: const Duration(seconds: 2),
    );
  }

  void copyAllLogs() {
    final list = filteredEntries;
    if (list.isEmpty) {
      Get.snackbar(
        'Log Kosong',
        'Tidak ada baris log yang dapat disalin.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return;
    }

    final allText = list.map((e) {
      final ts = e.timestamp != null ? '[${e.timestamp!.toIso8601String()}] ' : '';
      return '$ts[${e.priority}] ${e.message}';
    }).join('\n');

    Clipboard.setData(ClipboardData(text: allText));
    Get.snackbar(
      'Seluruh Log Tersalin',
      '${list.length} baris log berhasil disalin ke clipboard.',
      snackPosition: SnackPosition.BOTTOM,
      backgroundColor: const Color(0xFF1E293B),
      colorText: Colors.tealAccent,
      duration: const Duration(seconds: 3),
    );
  }
}
