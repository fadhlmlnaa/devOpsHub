class ServiceModel {
  final String name;
  final String loadState;
  final String activeState;
  final String subState;
  final String? description;
  final bool? enabled;
  final int? mainPid;
  final String? activeEnterTimestamp;
  final DateTime? checkedAt;

  ServiceModel({
    required this.name,
    required this.loadState,
    required this.activeState,
    required this.subState,
    this.description,
    this.enabled,
    this.mainPid,
    this.activeEnterTimestamp,
    this.checkedAt,
  });

  String get status {
    final active = activeState.toLowerCase();
    final sub = subState.toLowerCase();

    if (active == 'active') {
      return 'RUNNING';
    } else if (active == 'failed' || sub == 'failed') {
      return 'FAILED';
    } else if (active == 'inactive' || sub == 'dead' || sub == 'exited' || sub == 'stop') {
      return 'STOPPED';
    }
    return 'UNKNOWN';
  }

  bool get isRunning => status == 'RUNNING';
  bool get isStopped => status == 'STOPPED';
  bool get isFailed => status == 'FAILED';

  factory ServiceModel.fromJson(Map<String, dynamic> json) {
    return ServiceModel(
      name: json['name'] as String? ?? '',
      loadState: json['load_state'] as String? ?? 'unknown',
      activeState: json['active_state'] as String? ?? 'unknown',
      subState: json['sub_state'] as String? ?? 'unknown',
      description: json['description'] as String?,
      enabled: json['enabled'] as bool?,
      mainPid: json['main_pid'] as int?,
      activeEnterTimestamp: json['active_enter_timestamp'] as String?,
      checkedAt: json['checked_at'] != null
          ? DateTime.tryParse(json['checked_at'].toString())?.toLocal()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'load_state': loadState,
      'active_state': activeState,
      'sub_state': subState,
      if (description != null) 'description': description,
      if (enabled != null) 'enabled': enabled,
      if (mainPid != null) 'main_pid': mainPid,
      if (activeEnterTimestamp != null) 'active_enter_timestamp': activeEnterTimestamp,
      if (checkedAt != null) 'checked_at': checkedAt!.toIso8601String(),
    };
  }
}

class ServiceListModel {
  final String serverId;
  final bool systemdSupported;
  final List<ServiceModel> services;
  final DateTime checkedAt;
  final String? message;

  ServiceListModel({
    required this.serverId,
    required this.systemdSupported,
    required this.services,
    required this.checkedAt,
    this.message,
  });

  factory ServiceListModel.fromJson(Map<String, dynamic> json) {
    final list = json['services'] as List<dynamic>? ?? [];
    return ServiceListModel(
      serverId: json['server_id'] as String? ?? '',
      systemdSupported: json['systemd_supported'] as bool? ?? false,
      services: list.map((e) => ServiceModel.fromJson(e as Map<String, dynamic>)).toList(),
      checkedAt: DateTime.tryParse(json['checked_at']?.toString() ?? '')?.toLocal() ?? DateTime.now(),
      message: json['message'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'server_id': serverId,
      'systemd_supported': systemdSupported,
      'services': services.map((e) => e.toJson()).toList(),
      'checked_at': checkedAt.toIso8601String(),
      if (message != null) 'message': message,
    };
  }
}

class ServiceStateSummaryModel {
  final String activeState;
  final String subState;

  ServiceStateSummaryModel({
    required this.activeState,
    required this.subState,
  });

  factory ServiceStateSummaryModel.fromJson(Map<String, dynamic> json) {
    return ServiceStateSummaryModel(
      activeState: json['active_state'] as String? ?? 'unknown',
      subState: json['sub_state'] as String? ?? 'unknown',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'active_state': activeState,
      'sub_state': subState,
    };
  }
}

class ServiceActionResultModel {
  final bool success;
  final String service;
  final String action;
  final ServiceStateSummaryModel? previousState;
  final ServiceStateSummaryModel? currentState;
  final String message;
  final DateTime checkedAt;

  ServiceActionResultModel({
    required this.success,
    required this.service,
    required this.action,
    this.previousState,
    this.currentState,
    required this.message,
    required this.checkedAt,
  });

  factory ServiceActionResultModel.fromJson(Map<String, dynamic> json) {
    return ServiceActionResultModel(
      success: json['success'] as bool? ?? false,
      service: json['service'] as String? ?? '',
      action: json['action'] as String? ?? '',
      previousState: json['previous_state'] != null
          ? ServiceStateSummaryModel.fromJson(json['previous_state'] as Map<String, dynamic>)
          : null,
      currentState: json['current_state'] != null
          ? ServiceStateSummaryModel.fromJson(json['current_state'] as Map<String, dynamic>)
          : null,
      message: json['message'] as String? ?? '',
      checkedAt: DateTime.tryParse(json['checked_at']?.toString() ?? '')?.toLocal() ?? DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'service': service,
      'action': action,
      if (previousState != null) 'previous_state': previousState!.toJson(),
      if (currentState != null) 'current_state': currentState!.toJson(),
      'message': message,
      'checked_at': checkedAt.toIso8601String(),
    };
  }
}
