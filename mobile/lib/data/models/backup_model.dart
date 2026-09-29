class BackupConfigModel {
  final String id;
  final String workspaceId;
  final String environmentId;
  final String serverId;
  final String name;
  final String? description;
  final String backupType; // "POSTGRESQL", "FILESYSTEM", "DOCKER_VOLUME"
  final String source;
  final String destination;
  final int retentionDays;
  final bool isCompressed;
  final bool isActive;
  final String? environmentName;
  final bool environmentIsProtected;
  final String? serverName;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  BackupConfigModel({
    required this.id,
    required this.workspaceId,
    required this.environmentId,
    required this.serverId,
    required this.name,
    this.description,
    this.backupType = 'POSTGRESQL',
    required this.source,
    required this.destination,
    this.retentionDays = 7,
    this.isCompressed = true,
    this.isActive = true,
    this.environmentName,
    this.environmentIsProtected = false,
    this.serverName,
    this.createdAt,
    this.updatedAt,
  });

  bool get isPostgreSQL => backupType.toUpperCase() == 'POSTGRESQL';
  bool get isPostgres => isPostgreSQL;
  bool get isFilesystem => backupType.toUpperCase() == 'FILESYSTEM';
  bool get isDockerVolume => backupType.toUpperCase() == 'DOCKER_VOLUME';

  String get backupTypeFormatted {
    switch (backupType.toUpperCase()) {
      case 'POSTGRESQL':
        return 'PostgreSQL';
      case 'FILESYSTEM':
        return 'Filesystem';
      case 'DOCKER_VOLUME':
        return 'Docker Volume';
      default:
        return backupType;
    }
  }

  factory BackupConfigModel.fromJson(Map<String, dynamic> json) {
    return BackupConfigModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      environmentId: json['environment_id']?.toString() ?? '',
      serverId: json['server_id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      description: json['description'] as String?,
      backupType: json['backup_type']?.toString() ?? 'POSTGRESQL',
      source: json['source']?.toString() ?? '',
      destination: json['destination']?.toString() ?? '',
      retentionDays: json['retention_days'] as int? ?? 7,
      isCompressed: json['is_compressed'] as bool? ?? true,
      isActive: json['is_active'] as bool? ?? true,
      environmentName: json['environment_name'] as String?,
      environmentIsProtected: json['environment_is_protected'] as bool? ?? false,
      serverName: json['server_name'] as String?,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'workspace_id': workspaceId,
      'environment_id': environmentId,
      'server_id': serverId,
      'name': name,
      'description': description,
      'backup_type': backupType,
      'source': source,
      'destination': destination,
      'retention_days': retentionDays,
      'is_compressed': isCompressed,
      'is_active': isActive,
    };
  }
}


class BackupModel {
  final String id;
  final String workspaceId;
  final String environmentId;
  final String serverId;
  final String backupConfigId;
  final String status; // "PENDING", "RUNNING", "SUCCESS", "FAILED", "CANCELLED"
  final DateTime startedAt;
  final DateTime? finishedAt;
  final String? fileName;
  final String? filePath;
  final int? fileSizeBytes;
  final String? checksum;
  final String? errorMessage;
  final String? triggeredByUserId;
  final DateTime createdAt;

  final String? backupConfigName;
  final String? backupType;
  final String? environmentName;
  final bool environmentIsProtected;
  final String? serverName;
  final String? triggeredByName;

  BackupModel({
    required this.id,
    required this.workspaceId,
    required this.environmentId,
    required this.serverId,
    required this.backupConfigId,
    required this.status,
    required this.startedAt,
    this.finishedAt,
    this.fileName,
    this.filePath,
    this.fileSizeBytes,
    this.checksum,
    this.errorMessage,
    this.triggeredByUserId,
    required this.createdAt,
    this.backupConfigName,
    this.backupType,
    this.environmentName,
    this.environmentIsProtected = false,
    this.serverName,
    this.triggeredByName,
  });

  bool get isSuccess => status.toUpperCase() == 'SUCCESS';
  bool get isRunning => status.toUpperCase() == 'RUNNING' || status.toUpperCase() == 'PENDING';
  bool get isFailed => status.toUpperCase() == 'FAILED';

  String get formattedSize {
    if (fileSizeBytes == null || fileSizeBytes! <= 0) return '0 B';
    const suffixes = ['B', 'KB', 'MB', 'GB', 'TB'];
    var i = 0;
    double bytes = fileSizeBytes!.toDouble();
    while (bytes >= 1024 && i < suffixes.length - 1) {
      bytes /= 1024;
      i++;
    }
    return '${bytes.toStringAsFixed(1)} ${suffixes[i]}';
  }

  String get formattedFileSize => formattedSize;

  String get checksumSnippet {
    if (checksum == null || checksum!.isEmpty) return '-';
    if (checksum!.length <= 12) return checksum!;
    return '${checksum!.substring(0, 8)}...${checksum!.substring(checksum!.length - 4)}';
  }

  String get durationFormatted {
    if (finishedAt == null) return '-';
    final dur = finishedAt!.difference(startedAt);
    if (dur.isNegative) return '-';
    if (dur.inMinutes > 0) {
      final secs = dur.inSeconds % 60;
      return '${dur.inMinutes}m ${secs}s';
    }
    return '${dur.inSeconds}s';
  }

  factory BackupModel.fromJson(Map<String, dynamic> json) {
    return BackupModel(
      id: json['id']?.toString() ?? '',
      workspaceId: json['workspace_id']?.toString() ?? '',
      environmentId: json['environment_id']?.toString() ?? '',
      serverId: json['server_id']?.toString() ?? '',
      backupConfigId: json['backup_config_id']?.toString() ?? '',
      status: json['status']?.toString() ?? 'PENDING',
      startedAt: json['started_at'] != null
          ? DateTime.tryParse(json['started_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      finishedAt: json['finished_at'] != null ? DateTime.tryParse(json['finished_at'].toString()) : null,
      fileName: json['file_name'] as String?,
      filePath: json['file_path'] as String?,
      fileSizeBytes: json['file_size_bytes'] as int?,
      checksum: json['checksum'] as String?,
      errorMessage: json['error_message'] as String?,
      triggeredByUserId: json['triggered_by_user_id']?.toString(),
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      backupConfigName: json['backup_config_name'] as String?,
      backupType: json['backup_type'] as String?,
      environmentName: json['environment_name'] as String?,
      environmentIsProtected: json['environment_is_protected'] as bool? ?? false,
      serverName: json['server_name'] as String?,
      triggeredByName: json['triggered_by_name'] as String?,
    );
  }
}


class BackupLogEntryModel {
  final int sequence;
  final DateTime? timestamp;
  final String level; // "INFO", "WARNING", "ERROR"
  final String message;

  BackupLogEntryModel({
    required this.sequence,
    this.timestamp,
    required this.level,
    required this.message,
  });

  bool get isError => level.toUpperCase() == 'ERROR';
  bool get isWarning => level.toUpperCase() == 'WARNING';
  bool get isInfo => level.toUpperCase() == 'INFO';

  factory BackupLogEntryModel.fromJson(Map<String, dynamic> json) {
    return BackupLogEntryModel(
      sequence: json['sequence'] as int? ?? 0,
      timestamp: json['timestamp'] != null ? DateTime.tryParse(json['timestamp'].toString()) : null,
      level: json['level']?.toString() ?? 'INFO',
      message: json['message']?.toString() ?? '',
    );
  }
}


class BackupLogsModel {
  final String backupId;
  final String status;
  final int linesReturned;
  final List<BackupLogEntryModel> entries;

  BackupLogsModel({
    required this.backupId,
    required this.status,
    required this.linesReturned,
    required this.entries,
  });

  factory BackupLogsModel.fromJson(Map<String, dynamic> json) {
    return BackupLogsModel(
      backupId: json['backup_id']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      linesReturned: json['lines_returned'] as int? ?? 0,
      entries: (json['entries'] as List<dynamic>?)
              ?.map((e) => BackupLogEntryModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}


class BackupVerifyResultModel {
  final String backupId;
  final bool verified;
  final String? storedChecksum;
  final String? calculatedChecksum;
  final bool fileExists;
  final DateTime? verifiedAt;
  final String message;

  String? get checksum => calculatedChecksum ?? storedChecksum;

  BackupVerifyResultModel({
    required this.backupId,
    required this.verified,
    this.storedChecksum,
    this.calculatedChecksum,
    required this.fileExists,
    this.verifiedAt,
    required this.message,
  });

  factory BackupVerifyResultModel.fromJson(Map<String, dynamic> json) {
    final chk = json['checksum'] as String?;
    return BackupVerifyResultModel(
      backupId: json['backup_id']?.toString() ?? '',
      verified: json['verified'] as bool? ?? false,
      storedChecksum: json['stored_checksum'] as String? ?? chk,
      calculatedChecksum: json['calculated_checksum'] as String? ?? chk,
      fileExists: json['file_exists'] as bool? ?? false,
      verifiedAt: json['verified_at'] != null ? DateTime.tryParse(json['verified_at'].toString()) : null,
      message: json['message']?.toString() ?? '',
    );
  }
}
