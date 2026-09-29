class LogEntryModel {
  final DateTime? timestamp;
  final String priority;
  final String message;

  LogEntryModel({
    this.timestamp,
    required this.priority,
    required this.message,
  });

  factory LogEntryModel.fromJson(Map<String, dynamic> json) {
    return LogEntryModel(
      timestamp: json['timestamp'] != null
          ? DateTime.tryParse(json['timestamp'].toString())?.toLocal()
          : null,
      priority: json['priority'] as String? ?? 'INFO',
      message: json['message'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (timestamp != null) 'timestamp': timestamp!.toIso8601String(),
      'priority': priority,
      'message': message,
    };
  }
}

class LogResponseModel {
  final String serverId;
  final String service;
  final int linesRequested;
  final int linesReturned;
  final String? since;
  final bool truncated;
  final List<LogEntryModel> entries;
  final DateTime checkedAt;

  LogResponseModel({
    required this.serverId,
    required this.service,
    required this.linesRequested,
    required this.linesReturned,
    this.since,
    this.truncated = false,
    required this.entries,
    required this.checkedAt,
  });

  factory LogResponseModel.fromJson(Map<String, dynamic> json) {
    final list = json['entries'] as List<dynamic>? ?? [];
    return LogResponseModel(
      serverId: json['server_id'] as String? ?? '',
      service: json['service'] as String? ?? '',
      linesRequested: json['lines_requested'] as int? ?? 100,
      linesReturned: json['lines_returned'] as int? ?? 0,
      since: json['since'] as String?,
      truncated: json['truncated'] as bool? ?? false,
      entries: list.map((e) => LogEntryModel.fromJson(e as Map<String, dynamic>)).toList(),
      checkedAt: DateTime.tryParse(json['checked_at']?.toString() ?? '')?.toLocal() ?? DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'server_id': serverId,
      'service': service,
      'lines_requested': linesRequested,
      'lines_returned': linesReturned,
      if (since != null) 'since': since,
      'truncated': truncated,
      'entries': entries.map((e) => e.toJson()).toList(),
      'checked_at': checkedAt.toIso8601String(),
    };
  }
}
