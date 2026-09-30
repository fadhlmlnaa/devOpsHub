import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/secure_storage_service.dart';

enum TerminalState { connecting, connected, disconnected, error }

class TerminalController extends GetxController {
  final String workspaceId;
  final String serverId;
  final String serverName;
  final String host;
  final String? username;

  final Rx<TerminalState> state = TerminalState.connecting.obs;
  final RxString statusMessage = 'Menghubungkan ke PTY...'.obs;
  final RxList<String> outputLines = <String>[].obs;
  final RxString currentRawBuffer = ''.obs;

  WebSocket? _webSocket;
  StreamSubscription? _subscription;
  final ScrollController scrollController = ScrollController();

  TerminalController({
    required this.workspaceId,
    required this.serverId,
    required this.serverName,
    required this.host,
    this.username,
  });

  @override
  void onInit() {
    super.onInit();
    connect();
  }

  @override
  void onClose() {
    disconnect();
    scrollController.dispose();
    super.onClose();
  }

  Future<void> connect() async {
    disconnect();
    state.value = TerminalState.connecting;
    statusMessage.value = 'Menghubungkan...';
    outputLines.clear();
    currentRawBuffer.value = '';

    try {
      final secureStorage = Get.find<SecureStorageService>();
      final token = await secureStorage.getAccessToken();

      if (token == null) {
        state.value = TerminalState.error;
        statusMessage.value = 'Sesi tidak valid';
        _appendOutput('[DevOpsHub] Error: Token autentikasi tidak ditemukan.\n');
        return;
      }

      final apiClient = Get.find<ApiClient>();
      final baseUrl = apiClient.dio.options.baseUrl.isNotEmpty
          ? apiClient.dio.options.baseUrl
          : AppConstants.baseUrl; // e.g. http://127.0.0.1:8000/api/v1
      final wsBaseUrl = baseUrl
          .replaceFirst('https://', 'wss://')
          .replaceFirst('http://', 'ws://');

      final wsUrl = '$wsBaseUrl/workspaces/$workspaceId/servers/$serverId/terminal/ws?token=$token&cols=80&rows=25';

      _webSocket = await WebSocket.connect(wsUrl).timeout(const Duration(seconds: 15));

      state.value = TerminalState.connected;
      statusMessage.value = 'Live PTY Connected';

      _subscription = _webSocket!.listen(
        (data) {
          final text = data.toString();
          _appendOutput(text);
        },
        onError: (err) {
          state.value = TerminalState.error;
          statusMessage.value = 'Koneksi error';
          _appendOutput('\n[DevOpsHub] Error koneksi: $err\n');
        },
        onDone: () {
          state.value = TerminalState.disconnected;
          statusMessage.value = 'Terputus';
          _appendOutput('\n[DevOpsHub] Sesi terminal ditutup oleh server.\n');
        },
      );
    } catch (e) {
      state.value = TerminalState.error;
      statusMessage.value = 'Gagal terhubung';
      _appendOutput('\n[DevOpsHub] Gagal menghubungkan terminal: $e\n');
    }
  }

  void disconnect() {
    _subscription?.cancel();
    _subscription = null;
    _webSocket?.close();
    _webSocket = null;
    state.value = TerminalState.disconnected;
  }

  void _appendOutput(String chunk) {
    currentRawBuffer.value += chunk;

    // Split lines preserving formatting
    final split = currentRawBuffer.value.split('\n');
    if (split.length > 1) {
      for (int i = 0; i < split.length - 1; i++) {
        outputLines.add(split[i]);
      }
      currentRawBuffer.value = split.last;
    }

    // Keep maximum 1000 lines in history
    if (outputLines.length > 1000) {
      outputLines.removeRange(0, outputLines.length - 1000);
    }

    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (scrollController.hasClients) {
        scrollController.animateTo(
          scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 80),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void sendInput(String text) {
    if (state.value != TerminalState.connected || _webSocket == null) return;
    _webSocket!.add(text);
  }

  void sendCommand(String cmd) {
    sendInput('$cmd\n');
  }

  void sendKey(String key) {
    switch (key) {
      case 'CTRL_C':
        sendInput('\x03');
        break;
      case 'CTRL_D':
        sendInput('\x04');
        break;
      case 'CTRL_Z':
        sendInput('\x1a');
        break;
      case 'CTRL_L':
        sendInput('\x0c');
        break;
      case 'TAB':
        sendInput('\t');
        break;
      case 'ESC':
        sendInput('\x1b');
        break;
      case 'UP':
        sendInput('\x1b[A');
        break;
      case 'DOWN':
        sendInput('\x1b[B');
        break;
      case 'RIGHT':
        sendInput('\x1b[C');
        break;
      case 'LEFT':
        sendInput('\x1b[D');
        break;
      default:
        sendInput(key);
    }
  }

  void clearScreen() {
    outputLines.clear();
    currentRawBuffer.value = '';
    sendInput('\x0c'); // Send CTRL+L to clear remote screen as well
  }

  String get fullCleanOutput {
    final all = [...outputLines, currentRawBuffer.value].join('\n');
    // Strip ANSI codes for clean clipboard copy
    return all.replaceAll(RegExp(r'\x1B\[[0-?]*[ -/]*[@-~]'), '');
  }
}
