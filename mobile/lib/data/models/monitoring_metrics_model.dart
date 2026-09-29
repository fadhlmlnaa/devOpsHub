class CPUMetricsModel {
  final double? usagePercent;
  final int? cores;
  final String? error;

  CPUMetricsModel({this.usagePercent, this.cores, this.error});

  factory CPUMetricsModel.fromJson(Map<String, dynamic> json) {
    return CPUMetricsModel(
      usagePercent: json['usage_percent'] != null ? (json['usage_percent'] as num).toDouble() : null,
      cores: json['cores'] as int?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'usage_percent': usagePercent,
        'cores': cores,
        'error': error,
      };
}

class MemoryMetricsModel {
  final int? totalBytes;
  final int? usedBytes;
  final int? availableBytes;
  final int? freeBytes;
  final double? usagePercent;
  final String? error;

  MemoryMetricsModel({
    this.totalBytes,
    this.usedBytes,
    this.availableBytes,
    this.freeBytes,
    this.usagePercent,
    this.error,
  });

  factory MemoryMetricsModel.fromJson(Map<String, dynamic> json) {
    return MemoryMetricsModel(
      totalBytes: json['total_bytes'] as int?,
      usedBytes: json['used_bytes'] as int?,
      availableBytes: json['available_bytes'] as int?,
      freeBytes: json['free_bytes'] as int?,
      usagePercent: json['usage_percent'] != null ? (json['usage_percent'] as num).toDouble() : null,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'total_bytes': totalBytes,
        'used_bytes': usedBytes,
        'available_bytes': availableBytes,
        'free_bytes': freeBytes,
        'usage_percent': usagePercent,
        'error': error,
      };
}

class DiskMetricsModel {
  final String? filesystem;
  final String mountPoint;
  final int? totalBytes;
  final int? usedBytes;
  final int? availableBytes;
  final double? usagePercent;
  final String? error;

  DiskMetricsModel({
    this.filesystem,
    this.mountPoint = '/',
    this.totalBytes,
    this.usedBytes,
    this.availableBytes,
    this.usagePercent,
    this.error,
  });

  factory DiskMetricsModel.fromJson(Map<String, dynamic> json) {
    return DiskMetricsModel(
      filesystem: json['filesystem'] as String?,
      mountPoint: json['mount_point'] as String? ?? '/',
      totalBytes: json['total_bytes'] as int?,
      usedBytes: json['used_bytes'] as int?,
      availableBytes: json['available_bytes'] as int?,
      usagePercent: json['usage_percent'] != null ? (json['usage_percent'] as num).toDouble() : null,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'filesystem': filesystem,
        'mount_point': mountPoint,
        'total_bytes': totalBytes,
        'used_bytes': usedBytes,
        'available_bytes': availableBytes,
        'usage_percent': usagePercent,
        'error': error,
      };
}

class LoadMetricsModel {
  final double? load1m;
  final double? load5m;
  final double? load15m;
  final String? error;

  LoadMetricsModel({
    this.load1m,
    this.load5m,
    this.load15m,
    this.error,
  });

  factory LoadMetricsModel.fromJson(Map<String, dynamic> json) {
    return LoadMetricsModel(
      load1m: json['load_1m'] != null ? (json['load_1m'] as num).toDouble() : null,
      load5m: json['load_5m'] != null ? (json['load_5m'] as num).toDouble() : null,
      load15m: json['load_15m'] != null ? (json['load_15m'] as num).toDouble() : null,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'load_1m': load1m,
        'load_5m': load5m,
        'load_15m': load15m,
        'error': error,
      };
}

class SystemInfoMetricsModel {
  final String? hostname;
  final String? operatingSystem;
  final String? kernel;
  final String? architecture;
  final String? error;

  SystemInfoMetricsModel({
    this.hostname,
    this.operatingSystem,
    this.kernel,
    this.architecture,
    this.error,
  });

  factory SystemInfoMetricsModel.fromJson(Map<String, dynamic> json) {
    return SystemInfoMetricsModel(
      hostname: json['hostname'] as String?,
      operatingSystem: json['operating_system'] as String?,
      kernel: json['kernel'] as String?,
      architecture: json['architecture'] as String?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'hostname': hostname,
        'operating_system': operatingSystem,
        'kernel': kernel,
        'architecture': architecture,
        'error': error,
      };
}

class NetworkInterfaceModel {
  final String name;
  final List<String> addresses;

  NetworkInterfaceModel({required this.name, required this.addresses});

  factory NetworkInterfaceModel.fromJson(Map<String, dynamic> json) {
    final addrs = json['addresses'] is List
        ? (json['addresses'] as List).map((e) => e.toString()).toList()
        : <String>[];
    return NetworkInterfaceModel(
      name: json['name']?.toString() ?? '',
      addresses: addrs,
    );
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        'addresses': addresses,
      };
}

class NetworkMetricsModel {
  final List<NetworkInterfaceModel> interfaces;
  final String? error;

  NetworkMetricsModel({this.interfaces = const [], this.error});

  factory NetworkMetricsModel.fromJson(Map<String, dynamic> json) {
    final list = json['interfaces'] is List
        ? (json['interfaces'] as List)
            .map((e) => NetworkInterfaceModel.fromJson(e as Map<String, dynamic>))
            .toList()
        : <NetworkInterfaceModel>[];
    return NetworkMetricsModel(
      interfaces: list,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'interfaces': interfaces.map((e) => e.toJson()).toList(),
        'error': error,
      };
}

class ServerMetricsModel {
  final String serverId;
  final String status; // ONLINE, OFFLINE, UNKNOWN
  final DateTime checkedAt;
  final CPUMetricsModel? cpu;
  final MemoryMetricsModel? memory;
  final DiskMetricsModel? disk;
  final LoadMetricsModel? load;
  final int? uptimeSeconds;
  final SystemInfoMetricsModel? system;
  final NetworkMetricsModel? network;
  final String? message;
  final String? error;

  ServerMetricsModel({
    required this.serverId,
    required this.status,
    required this.checkedAt,
    this.cpu,
    this.memory,
    this.disk,
    this.load,
    this.uptimeSeconds,
    this.system,
    this.network,
    this.message,
    this.error,
  });

  factory ServerMetricsModel.fromJson(Map<String, dynamic> json) {
    return ServerMetricsModel(
      serverId: json['server_id']?.toString() ?? '',
      status: json['status'] as String? ?? 'UNKNOWN',
      checkedAt: json['checked_at'] != null
          ? (DateTime.tryParse(json['checked_at'].toString()) ?? DateTime.now())
          : DateTime.now(),
      cpu: json['cpu'] is Map<String, dynamic> ? CPUMetricsModel.fromJson(json['cpu'] as Map<String, dynamic>) : null,
      memory: json['memory'] is Map<String, dynamic> ? MemoryMetricsModel.fromJson(json['memory'] as Map<String, dynamic>) : null,
      disk: json['disk'] is Map<String, dynamic> ? DiskMetricsModel.fromJson(json['disk'] as Map<String, dynamic>) : null,
      load: json['load'] is Map<String, dynamic> ? LoadMetricsModel.fromJson(json['load'] as Map<String, dynamic>) : null,
      uptimeSeconds: json['uptime_seconds'] as int?,
      system: json['system'] is Map<String, dynamic> ? SystemInfoMetricsModel.fromJson(json['system'] as Map<String, dynamic>) : null,
      network: json['network'] is Map<String, dynamic> ? NetworkMetricsModel.fromJson(json['network'] as Map<String, dynamic>) : null,
      message: json['message'] as String?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'server_id': serverId,
        'status': status,
        'checked_at': checkedAt.toIso8601String(),
        'cpu': cpu?.toJson(),
        'memory': memory?.toJson(),
        'disk': disk?.toJson(),
        'load': load?.toJson(),
        'uptime_seconds': uptimeSeconds,
        'system': system?.toJson(),
        'network': network?.toJson(),
        'message': message,
        'error': error,
      };
}
