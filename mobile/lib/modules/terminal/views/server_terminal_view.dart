import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/app_app_bar.dart';
import '../controllers/terminal_controller.dart';

class ServerTerminalView extends StatefulWidget {
  const ServerTerminalView({super.key});

  @override
  State<ServerTerminalView> createState() => _ServerTerminalViewState();
}

class _ServerTerminalViewState extends State<ServerTerminalView> {
  late final TerminalController controller;
  final TextEditingController _inputController = TextEditingController();
  final FocusNode _inputFocusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    final args = Get.arguments as Map<String, dynamic>? ?? {};
    final params = Get.parameters;

    final workspaceId = args['workspaceId']?.toString() ?? params['id'] ?? '';
    final serverId = args['serverId']?.toString() ?? params['serverId'] ?? '';
    final serverName = args['serverName']?.toString() ?? 'Server Terminal';
    final host = args['host']?.toString() ?? '';
    final username = args['username']?.toString();

    controller = Get.put(
      TerminalController(
        workspaceId: workspaceId,
        serverId: serverId,
        serverName: serverName,
        host: host,
        username: username,
      ),
      tag: serverId,
    );
  }

  @override
  void dispose() {
    _inputController.dispose();
    _inputFocusNode.dispose();
    super.dispose();
  }

  void _submitCommand() {
    final text = _inputController.text;
    if (text.isNotEmpty) {
      controller.sendCommand(text);
      _inputController.clear();
      _inputFocusNode.requestFocus();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppAppBar(
        title: '${controller.serverName} (PTY)',
        actions: [
          // Connection status chip
          Obx(() {
            final state = controller.state.value;
            Color dotColor;
            String label;

            switch (state) {
              case TerminalState.connected:
                dotColor = AppColors.success;
                label = 'LIVE';
                break;
              case TerminalState.connecting:
                dotColor = AppColors.warning;
                label = 'CONNECTING';
                break;
              case TerminalState.disconnected:
                dotColor = AppColors.textMuted;
                label = 'OFFLINE';
                break;
              case TerminalState.error:
                dotColor = AppColors.error;
                label = 'ERROR';
                break;
            }

            return Container(
              margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: dotColor.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: dotColor.withValues(alpha: 0.4)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle),
                  ),
                  const SizedBox(width: 5),
                  Text(
                    label,
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: dotColor),
                  ),
                ],
              ),
            );
          }),
          // Reconnect button
          IconButton(
            tooltip: 'Reconnect Terminal',
            icon: const Icon(Icons.refresh_rounded, color: AppColors.textSecondary, size: 20),
            onPressed: () => controller.connect(),
          ),
          // Clear Screen button
          IconButton(
            tooltip: 'Clear Screen',
            icon: const Icon(Icons.cleaning_services_rounded, color: AppColors.textSecondary, size: 18),
            onPressed: () => controller.clearScreen(),
          ),
          // Copy Output button
          IconButton(
            tooltip: 'Copy Output',
            icon: const Icon(Icons.copy_rounded, color: AppColors.textSecondary, size: 18),
            onPressed: () {
              final text = controller.fullCleanOutput;
              Clipboard.setData(ClipboardData(text: text));
              Get.snackbar(
                'Tersalin',
                'Output terminal disalin ke clipboard.',
                snackPosition: SnackPosition.BOTTOM,
                backgroundColor: AppColors.surfaceElevated,
                colorText: AppColors.textPrimary,
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Top Server Connection Info Banner
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              color: const Color(0xFF161B22),
              child: Row(
                children: [
                  const Icon(Icons.terminal_rounded, size: 14, color: AppColors.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${controller.username ?? "user"}@${controller.host.isNotEmpty ? controller.host : "ssh-target"} (xterm-256color)',
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.textSecondary,
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w600,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Obx(() => Text(
                    controller.statusMessage.value,
                    style: TextStyle(
                      fontSize: 10,
                      color: controller.state.value == TerminalState.connected
                          ? AppColors.success
                          : controller.state.value == TerminalState.error
                              ? AppColors.error
                              : AppColors.textMuted,
                    ),
                  )),
                ],
              ),
            ),

            // Terminal Screen Console (Scrollable Output)
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(12),
                color: const Color(0xFF0D1117),
                child: Obx(() {
                  final lines = controller.outputLines;
                  final rawBuffer = controller.currentRawBuffer.value;

                  return SelectionArea(
                    child: ListView.builder(
                      controller: controller.scrollController,
                      itemCount: lines.length + (rawBuffer.isNotEmpty ? 1 : 0),
                      itemBuilder: (context, index) {
                        final lineText = index < lines.length ? lines[index] : rawBuffer;
                        return _buildTerminalLine(lineText);
                      },
                    ),
                  );
                }),
              ),
            ),

            // Quick Snippets Toolbar
            _buildSnippetsBar(),

            // Virtual Keyboard Action Bar (Tab, Ctrl+C, Esc, Arrows, Symbols)
            _buildVirtualKeyBar(),

            // Interactive Input Bar
            _buildInputRow(),
          ],
        ),
      ),
    );
  }

  Widget _buildTerminalLine(String text) {
    // Simple & Clean ANSI color parser
    final spans = _parseAnsi(text);
    return RichText(
      text: TextSpan(
        style: const TextStyle(
          fontFamily: 'monospace',
          fontSize: 12,
          height: 1.3,
          color: Color(0xFFC9D1D9),
        ),
        children: spans,
      ),
    );
  }

  List<TextSpan> _parseAnsi(String text) {
    final spans = <TextSpan>[];
    final ansiRegex = RegExp(r'\x1B\[([0-9;]*)m');
    int lastEnd = 0;
    Color currentColor = const Color(0xFFC9D1D9);
    FontWeight currentWeight = FontWeight.normal;

    for (final match in ansiRegex.allMatches(text)) {
      if (match.start > lastEnd) {
        spans.add(TextSpan(
          text: text.substring(lastEnd, match.start),
          style: TextStyle(color: currentColor, fontWeight: currentWeight),
        ));
      }

      final codes = match.group(1)?.split(';') ?? [];
      for (final codeStr in codes) {
        final code = int.tryParse(codeStr) ?? 0;
        if (code == 0) {
          currentColor = const Color(0xFFC9D1D9);
          currentWeight = FontWeight.normal;
        } else if (code == 1) {
          currentWeight = FontWeight.bold;
        } else if (code >= 30 && code <= 37) {
          currentColor = _getAnsiColor(code);
        } else if (code >= 90 && code <= 97) {
          currentColor = _getAnsiBrightColor(code);
        }
      }
      lastEnd = match.end;
    }

    if (lastEnd < text.length) {
      spans.add(TextSpan(
        text: text.substring(lastEnd),
        style: TextStyle(color: currentColor, fontWeight: currentWeight),
      ));
    }

    if (spans.isEmpty) {
      spans.add(TextSpan(text: text));
    }

    return spans;
  }

  Color _getAnsiColor(int code) {
    switch (code) {
      case 30:
        return const Color(0xFF484F58); // Black
      case 31:
        return const Color(0xFFF85149); // Red
      case 32:
        return const Color(0xFF3FB950); // Green
      case 33:
        return const Color(0xFFD29922); // Yellow
      case 34:
        return const Color(0xFF58A6FF); // Blue
      case 35:
        return const Color(0xFFBC8CFF); // Magenta
      case 36:
        return const Color(0xFF39C5CF); // Cyan
      case 37:
        return const Color(0xFFC9D1D9); // White
      default:
        return const Color(0xFFC9D1D9);
    }
  }

  Color _getAnsiBrightColor(int code) {
    switch (code) {
      case 90:
        return const Color(0xFF6E7681); // Bright Black / Gray
      case 91:
        return const Color(0xFFFF7B72); // Bright Red
      case 92:
        return const Color(0xFF56D364); // Bright Green
      case 93:
        return const Color(0xFFE3B341); // Bright Yellow
      case 94:
        return const Color(0xFF79C0FF); // Bright Blue
      case 95:
        return const Color(0xFFD2A8FF); // Bright Magenta
      case 96:
        return const Color(0xFF56D4DD); // Bright Cyan
      case 97:
        return const Color(0xFFFFFFFF); // Bright White
      default:
        return const Color(0xFFFFFFFF);
    }
  }

  Widget _buildSnippetsBar() {
    final snippets = [
      'docker ps',
      'htop',
      'df -h',
      'free -m',
      'uptime',
      'systemctl status',
      'ip a',
      'journalctl -n 50',
      'uname -a',
      'clear',
    ];

    return Container(
      height: 38,
      color: const Color(0xFF161B22),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        itemCount: snippets.length,
        itemBuilder: (context, index) {
          final snippet = snippets[index];
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4.0),
            child: InkWell(
              onTap: () => controller.sendCommand(snippet),
              borderRadius: BorderRadius.circular(6),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF21262D),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: const Color(0xFF30363D)),
                ),
                child: Center(
                  child: Text(
                    snippet,
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildVirtualKeyBar() {
    final keys = [
      {'label': 'TAB', 'key': 'TAB'},
      {'label': 'CTRL+C', 'key': 'CTRL_C', 'color': AppColors.error},
      {'label': 'CTRL+D', 'key': 'CTRL_D'},
      {'label': 'CTRL+Z', 'key': 'CTRL_Z'},
      {'label': 'ESC', 'key': 'ESC'},
      {'label': '↑', 'key': 'UP'},
      {'label': '↓', 'key': 'DOWN'},
      {'label': '←', 'key': 'LEFT'},
      {'label': '→', 'key': 'RIGHT'},
      {'label': '|', 'key': '|'},
      {'label': '~', 'key': '~'},
      {'label': '/', 'key': '/'},
      {'label': '-', 'key': '-'},
      {'label': 'sudo', 'key': 'sudo '},
      {'label': '&&', 'key': ' && '},
    ];

    return Container(
      height: 42,
      color: const Color(0xFF0D1117),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: Color(0xFF30363D), width: 1),
          bottom: BorderSide(color: Color(0xFF30363D), width: 1),
        ),
      ),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        itemCount: keys.length,
        itemBuilder: (context, index) {
          final item = keys[index];
          final label = item['label'] as String;
          final key = item['key'] as String;
          final customColor = item['color'] as Color?;

          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 3.0),
            child: InkWell(
              onTap: () => controller.sendKey(key),
              borderRadius: BorderRadius.circular(6),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFF21262D),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: const Color(0xFF30363D)),
                ),
                child: Center(
                  child: Text(
                    label,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: customColor ?? const Color(0xFFC9D1D9),
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildInputRow() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      color: const Color(0xFF161B22),
      child: Row(
        children: [
          const Text(
            '\$ ',
            style: TextStyle(
              fontFamily: 'monospace',
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: AppColors.success,
            ),
          ),
          Expanded(
            child: TextField(
              controller: _inputController,
              focusNode: _inputFocusNode,
              style: const TextStyle(
                fontFamily: 'monospace',
                fontSize: 13,
                color: Colors.white,
              ),
              cursorColor: AppColors.primary,
              decoration: const InputDecoration(
                hintText: 'Ketik perintah shell Linux...',
                hintStyle: TextStyle(fontSize: 12, color: AppColors.textMuted),
                border: InputBorder.none,
                isDense: true,
                contentPadding: EdgeInsets.symmetric(vertical: 6),
              ),
              onSubmitted: (_) => _submitCommand(),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send_rounded, color: AppColors.primary, size: 20),
            onPressed: _submitCommand,
          ),
        ],
      ),
    );
  }
}
