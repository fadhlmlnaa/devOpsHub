import 'package:flutter/material.dart';

class LogFilterWidget extends StatelessWidget {
  final int selectedLines;
  final String? selectedSince;
  final ValueChanged<int> onLinesChanged;
  final ValueChanged<String?> onSinceChanged;

  const LogFilterWidget({
    super.key,
    required this.selectedLines,
    required this.selectedSince,
    required this.onLinesChanged,
    required this.onSinceChanged,
  });

  @override
  Widget build(BuildContext context) {
    const linesOptions = [50, 100, 200, 500, 1000];
    const sinceOptions = [
      {'key': null, 'label': 'Semua'},
      {'key': '5m', 'label': '5 Menit'},
      {'key': '10m', 'label': '10 Menit'},
      {'key': '30m', 'label': '30 Menit'},
      {'key': '1h', 'label': '1 Jam'},
      {'key': '6h', 'label': '6 Jam'},
      {'key': '24h', 'label': '24 Jam'},
    ];

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: const Color(0xFF1E293B),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Lines Selection Row
          Row(
            children: [
              const Text(
                'Baris:',
                style: TextStyle(color: Colors.white60, fontSize: 12, fontWeight: FontWeight.w600),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: linesOptions.map((lines) {
                      final isSelected = selectedLines == lines;
                      return Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(6),
                          onTap: () => onLinesChanged(lines),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? Colors.tealAccent.withValues(alpha: 0.2)
                                  : const Color(0xFF0F172A),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(
                                color: isSelected ? Colors.tealAccent : Colors.white12,
                              ),
                            ),
                            child: Text(
                              '$lines',
                              style: TextStyle(
                                color: isSelected ? Colors.tealAccent : Colors.white70,
                                fontSize: 11,
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              ),
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Since Selection Row
          Row(
            children: [
              const Text(
                'Waktu:',
                style: TextStyle(color: Colors.white60, fontSize: 12, fontWeight: FontWeight.w600),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: sinceOptions.map((opt) {
                      final key = opt['key'];
                      final label = opt['label'] ?? '';
                      final isSelected = selectedSince == key;
                      return Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(6),
                          onTap: () => onSinceChanged(key),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? Colors.tealAccent.withValues(alpha: 0.2)
                                  : const Color(0xFF0F172A),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(
                                color: isSelected ? Colors.tealAccent : Colors.white12,
                              ),
                            ),
                            child: Text(
                              label,
                              style: TextStyle(
                                color: isSelected ? Colors.tealAccent : Colors.white70,
                                fontSize: 11,
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              ),
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
