import 'package:flutter_test/flutter_test.dart';
import 'package:devops_hub/data/models/user_model.dart';
import 'package:devops_hub/data/models/auth_token_model.dart';
import 'package:devops_hub/data/models/workspace_model.dart';
import 'package:devops_hub/data/models/workspace_member_model.dart';

import 'package:devops_hub/data/models/environment_model.dart';
import 'package:devops_hub/data/models/server_model.dart';
import 'package:devops_hub/data/models/connection_test_model.dart';
import 'package:devops_hub/data/models/monitoring_metrics_model.dart';
import 'package:devops_hub/data/models/service_model.dart';
import 'package:devops_hub/data/models/log_model.dart';
import 'package:devops_hub/data/models/docker_model.dart';
import 'package:devops_hub/data/models/deployment_model.dart';
import 'package:devops_hub/data/models/backup_model.dart';
import 'package:devops_hub/data/models/alert_model.dart';
import 'package:devops_hub/data/models/audit_log_model.dart';
import 'package:devops_hub/core/utils/formatters.dart';

void main() {
  group('UserModel JSON serialization', () {
    test('fromJson creates valid UserModel with UUID', () {
      final json = {
        'id': '1880608b-2590-49e5-9b4a-886318e5ed91',
        'email': 'fadhil@example.com',
        'name': 'Fadhil Maulana',
        'is_active': true,
        'created_at': '2026-09-29T10:00:00Z',
        'updated_at': '2026-09-29T10:00:00Z',
      };

      final user = UserModel.fromJson(json);
      expect(user.id, '1880608b-2590-49e5-9b4a-886318e5ed91');
      expect(user.email, 'fadhil@example.com');
      expect(user.name, 'Fadhil Maulana');
      expect(user.isActive, true);
      expect(user.createdAt, isNotNull);
    });

    test('toJson produces correct Map', () {
      final user = UserModel(
        id: '2a7f8462-ba41-4687-9927-ac32d833ef48',
        email: 'user@test.com',
        name: 'Test User',
      );
      final map = user.toJson();
      expect(map['id'], '2a7f8462-ba41-4687-9927-ac32d833ef48');
      expect(map['email'], 'user@test.com');
      expect(map['name'], 'Test User');
    });
  });

  group('AuthTokenModel JSON serialization', () {
    test('fromJson parses tokens and optional user', () {
      final json = {
        'access_token': 'test_access_jwt',
        'refresh_token': 'test_refresh_token',
        'token_type': 'bearer',
        'user': {
          'id': '1880608b-2590-49e5-9b4a-886318e5ed91',
          'email': 'user@example.com',
          'name': 'User Ex',
          'is_active': true,
        },
      };

      final auth = AuthTokenModel.fromJson(json);
      expect(auth.accessToken, 'test_access_jwt');
      expect(auth.refreshToken, 'test_refresh_token');
      expect(auth.tokenType, 'bearer');
      expect(auth.user?.name, 'User Ex');
      expect(auth.user?.id, '1880608b-2590-49e5-9b4a-886318e5ed91');
    });
  });

  group('WorkspaceModel JSON serialization', () {
    test('fromJson parses workspace details and user role', () {
      final json = {
        'id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'name': 'PT Bintang',
        'description': 'Main production workspace',
        'timezone': 'Asia/Jakarta',
        'role': 'OWNER',
        'created_at': '2026-09-29T10:00:00Z',
      };

      final ws = WorkspaceModel.fromJson(json);
      expect(ws.id, 'c7b5a190-3204-4edb-b483-1e440b8438bf');
      expect(ws.name, 'PT Bintang');
      expect(ws.description, 'Main production workspace');
      expect(ws.timezone, 'Asia/Jakarta');
      expect(ws.role, 'OWNER');
    });
  });

  group('WorkspaceMemberModel JSON serialization', () {
    test('fromJson parses member info correctly', () {
      final json = {
        'id': 'e8d12345-6ef2-4f98-a400-b9af0c72a5ac',
        'user_id': 'f9876543-1fa5-407c-b276-f72f642f1491',
        'role': 'DEVELOPER',
        'user_email': 'dev@example.com',
        'user_name': 'Developer One',
      };

      final member = WorkspaceMemberModel.fromJson(json);
      expect(member.id, 'e8d12345-6ef2-4f98-a400-b9af0c72a5ac');
      expect(member.userId, 'f9876543-1fa5-407c-b276-f72f642f1491');
      expect(member.role, 'DEVELOPER');
      expect(member.userEmail, 'dev@example.com');
    });
  });

  group('EnvironmentModel JSON serialization', () {
    test('fromJson parses environment and server count', () {
      final json = {
        'id': 'b1e8471b-29c8-472e-8395-5dbd8f1e0691',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'name': 'Production',
        'key': 'production',
        'description': 'Production environment',
        'server_count': 3,
        'created_at': '2026-09-29T10:00:00Z',
      };

      final env = EnvironmentModel.fromJson(json);
      expect(env.id, 'b1e8471b-29c8-472e-8395-5dbd8f1e0691');
      expect(env.name, 'Production');
      expect(env.key, 'production');
      expect(env.serverCount, 3);
      expect(env.description, 'Production environment');
    });
  });

  group('ServerModel JSON serialization', () {
    test('fromJson parses server with nested environment and status', () {
      final json = {
        'id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'environment_id': 'b1e8471b-29c8-472e-8395-5dbd8f1e0691',
        'name': 'Production Odoo',
        'hostname': 'prod-odoo',
        'ip_address': '103.111.222.333',
        'ssh_port': 22,
        'username': 'ubuntu',
        'operating_system': 'Ubuntu 24.04',
        'description': 'Main ERP server',
        'is_active': true,
        'has_credential': true,
        'auth_type': 'PRIVATE_KEY',
        'status': 'ONLINE',
        'environment': {
          'id': 'b1e8471b-29c8-472e-8395-5dbd8f1e0691',
          'name': 'Production',
          'key': 'production',
        },
      };

      final server = ServerModel.fromJson(json);
      expect(server.id, '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c');
      expect(server.name, 'Production Odoo');
      expect(server.hostname, 'prod-odoo');
      expect(server.ipAddress, '103.111.222.333');
      expect(server.sshPort, 22);
      expect(server.username, 'ubuntu');
      expect(server.operatingSystem, 'Ubuntu 24.04');
      expect(server.hasCredential, true);
      expect(server.authType, 'PRIVATE_KEY');
      expect(server.status, 'ONLINE');
      expect(server.environment?.name, 'Production');
    });
  });

  group('ConnectionTestModel JSON serialization', () {
    test('fromJson parses success and system info', () {
      final json = {
        'success': true,
        'message': 'SSH connection successful',
        'status': 'ONLINE',
        'server_info': {
          'hostname': 'prod-odoo',
          'operating_system': 'Ubuntu 24.04 LTS',
          'kernel': '6.8.0-40-generic',
          'architecture': 'x86_64',
          'uptime': '18 days, 4 hours',
        },
      };

      final result = ConnectionTestModel.fromJson(json);
      expect(result.success, true);
      expect(result.message, 'SSH connection successful');
      expect(result.status, 'ONLINE');
      expect(result.serverInfo?['hostname'], 'prod-odoo');
      expect(result.serverInfo?['operating_system'], 'Ubuntu 24.04 LTS');
      expect(result.serverInfo?['kernel'], '6.8.0-40-generic');
      expect(result.serverInfo?['architecture'], 'x86_64');
      expect(result.serverInfo?['uptime'], '18 days, 4 hours');
    });
  });

  group('ServerMetricsModel JSON serialization', () {
    test('fromJson parses complete telemetry dataset', () {
      final json = {
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'status': 'ONLINE',
        'checked_at': '2026-09-29T10:00:00Z',
        'cpu': {
          'usage_percent': 34.5,
          'cores': 4,
        },
        'memory': {
          'total_bytes': 8589934592,
          'used_bytes': 4294967296,
          'available_bytes': 4294967296,
          'usage_percent': 50.0,
        },
        'disk': {
          'mount_point': '/',
          'total_bytes': 107374182400,
          'used_bytes': 75161927680,
          'available_bytes': 32212254720,
          'usage_percent': 70.0,
        },
        'load': {
          'load_1m': 0.82,
          'load_5m': 0.64,
          'load_15m': 0.51,
        },
        'uptime_seconds': 1555200,
        'system': {
          'hostname': 'prod-odoo',
          'operating_system': 'Ubuntu 24.04.3 LTS',
          'kernel': '6.8.0',
          'architecture': 'x86_64',
        },
        'network': {
          'interfaces': [
            {
              'name': 'eth0',
              'addresses': ['10.0.0.10'],
            },
          ],
        },
      };

      final metrics = ServerMetricsModel.fromJson(json);
      expect(metrics.serverId, '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c');
      expect(metrics.status, 'ONLINE');
      expect(metrics.cpu?.usagePercent, 34.5);
      expect(metrics.cpu?.cores, 4);
      expect(metrics.memory?.totalBytes, 8589934592);
      expect(metrics.memory?.usagePercent, 50.0);
      expect(metrics.disk?.mountPoint, '/');
      expect(metrics.disk?.usagePercent, 70.0);
      expect(metrics.load?.load1m, 0.82);
      expect(metrics.uptimeSeconds, 1555200);
      expect(metrics.system?.hostname, 'prod-odoo');
      expect(metrics.network?.interfaces.first.name, 'eth0');
    });
  });

  group('AppFormatters Utility Tests', () {
    test('formatBytes formats properly across scales', () {
      expect(AppFormatters.formatBytes(500), '500.0 B');
      expect(AppFormatters.formatBytes(1048576), '1.0 MB');
      expect(AppFormatters.formatBytes(8589934592), '8.0 GB');
      expect(AppFormatters.formatBytes(1099511627776), '1.0 TB');
      expect(AppFormatters.formatBytes(null), '0 B');
    });

    test('formatPercentage formats decimal percentages', () {
      expect(AppFormatters.formatPercentage(34.567), '34.6%');
      expect(AppFormatters.formatPercentage(100.0), '100.0%');
      expect(AppFormatters.formatPercentage(null), '-');
    });

    test('formatUptime formats seconds into human readable duration', () {
      expect(AppFormatters.formatUptime(86400 * 3 + 3600 * 2 + 60 * 15), '3d 2h 15m');
      expect(AppFormatters.formatUptime(3600 * 5), '5h');
      expect(AppFormatters.formatUptime(45), '45s');
      expect(AppFormatters.formatUptime(null), 'Baru menyala');
    });
  });

  group('ServiceModel & ServiceListModel JSON serialization', () {
    test('ServiceModel parses running, stopped, and failed states', () {
      final runningJson = {
        'name': 'nginx.service',
        'load_state': 'loaded',
        'active_state': 'active',
        'sub_state': 'running',
        'description': 'A high performance web server',
        'enabled': true,
        'main_pid': 1234,
      };

      final failedJson = {
        'name': 'odoo.service',
        'load_state': 'loaded',
        'active_state': 'failed',
        'sub_state': 'failed',
        'description': 'Odoo ERP Server',
        'enabled': true,
      };

      final stoppedJson = {
        'name': 'redis.service',
        'load_state': 'loaded',
        'active_state': 'inactive',
        'sub_state': 'dead',
        'description': 'Redis In-Memory Data Store',
        'enabled': false,
      };

      final running = ServiceModel.fromJson(runningJson);
      expect(running.name, 'nginx.service');
      expect(running.status, 'RUNNING');
      expect(running.isRunning, true);
      expect(running.mainPid, 1234);

      final failed = ServiceModel.fromJson(failedJson);
      expect(failed.status, 'FAILED');
      expect(failed.isFailed, true);

      final stopped = ServiceModel.fromJson(stoppedJson);
      expect(stopped.status, 'STOPPED');
      expect(stopped.isStopped, true);
    });

    test('ServiceListModel parses full service response list', () {
      final json = {
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'systemd_supported': true,
        'services': [
          {
            'name': 'postgresql.service',
            'load_state': 'loaded',
            'active_state': 'active',
            'sub_state': 'running',
            'description': 'PostgreSQL Database Server',
            'enabled': true,
          }
        ],
        'checked_at': '2026-09-29T10:00:00Z',
      };

      final list = ServiceListModel.fromJson(json);
      expect(list.serverId, '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c');
      expect(list.systemdSupported, true);
      expect(list.services.length, 1);
      expect(list.services.first.name, 'postgresql.service');
    });

    test('ServiceActionResultModel parses start/restart responses', () {
      final json = {
        'success': true,
        'service': 'nginx.service',
        'action': 'restart',
        'previous_state': {'active_state': 'active', 'sub_state': 'running'},
        'current_state': {'active_state': 'active', 'sub_state': 'running'},
        'message': 'Service nginx.service berhasil di-restart.',
        'checked_at': '2026-09-29T10:00:00Z',
      };

      final actionRes = ServiceActionResultModel.fromJson(json);
      expect(actionRes.success, true);
      expect(actionRes.service, 'nginx.service');
      expect(actionRes.action, 'restart');
      expect(actionRes.currentState?.activeState, 'active');
    });
  });

  group('LogEntryModel & LogResponseModel JSON serialization', () {
    test('LogEntryModel parses timestamps and priorities correctly', () {
      final json = {
        'timestamp': '2026-09-29T10:30:00Z',
        'priority': 'ERROR',
        'message': 'Failed to bind to socket: address already in use',
      };

      final entry = LogEntryModel.fromJson(json);
      expect(entry.priority, 'ERROR');
      expect(entry.message, 'Failed to bind to socket: address already in use');
      expect(entry.timestamp, isNotNull);
    });

    test('LogResponseModel parses truncated state and entries array', () {
      final json = {
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'service': 'nginx.service',
        'lines_requested': 100,
        'lines_returned': 1,
        'since': '10m',
        'truncated': true,
        'entries': [
          {
            'timestamp': '2026-09-29T10:30:00Z',
            'priority': 'INFO',
            'message': 'Started nginx service.',
          }
        ],
        'checked_at': '2026-09-29T10:31:00Z',
      };

      final res = LogResponseModel.fromJson(json);
      expect(res.serverId, '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c');
      expect(res.service, 'nginx.service');
      expect(res.linesRequested, 100);
      expect(res.linesReturned, 1);
      expect(res.since, '10m');
      expect(res.truncated, true);
      expect(res.entries.length, 1);
      expect(res.entries.first.message, 'Started nginx service.');
    });
  });

  group('Docker Models JSON serialization', () {
    test('DockerStatusModel parses properly', () {
      final json = {
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'state': 'RUNNING',
        'installed': true,
        'running': true,
        'version': '28.0.1',
        'checked_at': '2026-09-29T10:30:00Z',
      };

      final status = DockerStatusModel.fromJson(json);
      expect(status.serverId, '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c');
      expect(status.state, 'RUNNING');
      expect(status.installed, true);
      expect(status.running, true);
      expect(status.version, '28.0.1');
    });

    test('DockerContainerModel parses container list item', () {
      final json = {
        'id': 'abc123456789',
        'name': 'web-nginx',
        'image': 'nginx:alpine',
        'status': 'Up 4 hours',
        'state': 'running',
        'created_at': '2026-09-29T06:00:00Z',
        'ports': ['80:80', '443:443'],
      };

      final container = DockerContainerModel.fromJson(json);
      expect(container.id, 'abc123456789');
      expect(container.name, 'web-nginx');
      expect(container.image, 'nginx:alpine');
      expect(container.isRunning, true);
      expect(container.ports.length, 2);
    });

    test('DockerContainerDetailModel parses details & restart policy', () {
      final json = {
        'id': 'abc123456789',
        'name': 'web-nginx',
        'image': 'nginx:alpine',
        'status': 'Up 4 hours',
        'state': 'running',
        'created_at': '2026-09-29T06:00:00Z',
        'started_at': '2026-09-29T06:00:05Z',
        'ports': ['80:80'],
        'restart_policy': 'unless-stopped',
        'cpu_usage': '0.5%',
        'memory_usage': '12.4MB / 1.0GB',
      };

      final detail = DockerContainerDetailModel.fromJson(json);
      expect(detail.restartPolicy, 'unless-stopped');
      expect(detail.cpuUsage, '0.5%');
      expect(detail.memoryUsage, '12.4MB / 1.0GB');
      expect(detail.isRunning, true);
    });

    test('DockerContainerActionResultModel parses container action outcome', () {
      final json = {
        'success': true,
        'container': 'web-nginx',
        'action': 'restart',
        'current_state': 'running',
        'message': 'Container web-nginx restarted successfully.',
        'checked_at': '2026-09-29T10:30:00Z',
      };

      final res = DockerContainerActionResultModel.fromJson(json);
      expect(res.success, true);
      expect(res.container, 'web-nginx');
      expect(res.action, 'restart');
      expect(res.currentState, 'running');
    });

    test('DockerContainerLogsModel parses log response with entries', () {
      final json = {
        'container': 'web-nginx',
        'lines_requested': 50,
        'lines_returned': 2,
        'since': '10m',
        'truncated': false,
        'entries': [
          {
            'timestamp': '2026-09-29T10:29:00Z',
            'message': 'GET /index.html 200',
          },
          {
            'timestamp': '2026-09-29T10:29:05Z',
            'message': 'GET /api/v1/health 200',
          }
        ],
        'checked_at': '2026-09-29T10:30:00Z',
      };

      final logs = DockerContainerLogsModel.fromJson(json);
      expect(logs.container, 'web-nginx');
      expect(logs.linesRequested, 50);
      expect(logs.linesReturned, 2);
      expect(logs.entries.length, 2);
      expect(logs.entries.first.message, 'GET /index.html 200');
    });

    test('DockerComposeProjectModel & DockerComposeStatusModel parse correctly', () {
      final projectJson = {
        'id': 'b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'environment_id': 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'name': 'PTBI Production',
        'project_name': 'ptbi',
        'working_directory': '/opt/apps/ptbi',
        'compose_file': 'docker-compose.yml',
        'description': 'Main PTBI application stack',
        'is_active': true,
        'created_at': '2026-09-29T00:00:00Z',
        'updated_at': '2026-09-29T00:00:00Z',
      };

      final project = DockerComposeProjectModel.fromJson(projectJson);
      expect(project.name, 'PTBI Production');
      expect(project.projectName, 'ptbi');
      expect(project.workingDirectory, '/opt/apps/ptbi');
      expect(project.composeFile, 'docker-compose.yml');

      final statusJson = {
        'project_id': 'b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'project_name': 'ptbi',
        'status': 'RUNNING',
        'services': [
          {'name': 'web', 'state': 'running'},
          {'name': 'db', 'state': 'running'},
        ],
        'checked_at': '2026-09-29T10:30:00Z',
      };

      final status = DockerComposeStatusModel.fromJson(statusJson);
      expect(status.projectId, 'b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d');
      expect(status.status, 'RUNNING');
      expect(status.services.length, 2);
      expect(status.services.first.name, 'web');
      expect(status.services.first.state, 'running');

      final actionJson = {
        'success': true,
        'project_id': 'b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'action': 'up',
        'status': 'RUNNING',
        'message': 'Docker compose project started successfully.',
        'checked_at': '2026-09-29T10:30:00Z',
      };

      final actionRes = DockerComposeActionResultModel.fromJson(actionJson);
      expect(actionRes.success, true);
      expect(actionRes.action, 'up');
      expect(actionRes.status, 'RUNNING');
    });
  });

  group('Deployment Models JSON serialization', () {
    test('DeploymentConfigModel parses accurately', () {
      final json = {
        'id': 'd1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'environment_id': 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'name': 'Odoo Production Deploy',
        'description': 'Main production deployment',
        'application_name': 'odoo',
        'working_directory': '/opt/odoo',
        'deployment_type': 'SYSTEMD',
        'branch': 'main',
        'restart_service_name': 'odoo.service',
        'is_active': true,
        'environment_name': 'Production',
        'environment_is_protected': true,
        'server_name': 'prod-01',
        'created_at': '2026-09-29T10:00:00Z',
      };

      final config = DeploymentConfigModel.fromJson(json);
      expect(config.id, 'd1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a');
      expect(config.name, 'Odoo Production Deploy');
      expect(config.isSystemd, true);
      expect(config.environmentIsProtected, true);
      expect(config.restartServiceName, 'odoo.service');
    });

    test('DeploymentModel parses history and execution attributes', () {
      final json = {
        'id': 'e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'environment_id': 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'deployment_config_id': 'd1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a',
        'status': 'SUCCESS',
        'triggered_by_user_id': '1880608b-2590-49e5-9b4a-886318e5ed91',
        'triggered_by_name': 'Fadhil Maulana',
        'commit_reference': 'a1b2c3d',
        'message': 'Deployment completed successfully.',
        'deployment_config_name': 'Odoo Production Deploy',
        'environment_name': 'Production',
        'environment_is_protected': true,
        'server_name': 'prod-01',
        'started_at': '2026-09-29T10:00:00Z',
        'finished_at': '2026-09-29T10:01:30Z',
        'created_at': '2026-09-29T10:00:00Z',
      };

      final dep = DeploymentModel.fromJson(json);
      expect(dep.id, 'e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b');
      expect(dep.status, 'SUCCESS');
      expect(dep.isSuccess, true);
      expect(dep.commitReference, 'a1b2c3d');
      expect(dep.triggeredByName, 'Fadhil Maulana');
    });

    test('DeploymentLogsModel & LogEntry parses stream and levels', () {
      final json = {
        'deployment_id': 'e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b',
        'status': 'RUNNING',
        'lines_returned': 2,
        'entries': [
          {
            'sequence': 1,
            'timestamp': '2026-09-29T10:00:00Z',
            'level': 'INFO',
            'message': 'Starting deployment workflow',
          },
          {
            'sequence': 2,
            'timestamp': '2026-09-29T10:00:05Z',
            'level': 'WARNING',
            'message': 'Package version notice',
          }
        ],
      };

      final logs = DeploymentLogsModel.fromJson(json);
      expect(logs.deploymentId, 'e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b');
      expect(logs.linesReturned, 2);
      expect(logs.entries.first.isInfo, true);
      expect(logs.entries.last.isWarning, true);
      expect(logs.entries.first.message, 'Starting deployment workflow');
    });
  });

  group('Backup Models JSON serialization', () {
    test('BackupConfigModel parses correctly', () {
      final json = {
        'id': 'f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'environment_id': 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'name': 'Production DB Backup',
        'description': 'Daily pg_dump backup',
        'backup_type': 'POSTGRESQL',
        'source': 'production_db',
        'destination': '/var/backups/postgresql',
        'retention_days': 14,
        'is_compressed': true,
        'is_active': true,
        'environment_name': 'Production',
        'environment_is_protected': true,
        'server_name': 'prod-01',
        'created_at': '2026-09-29T10:00:00Z',
      };

      final config = BackupConfigModel.fromJson(json);
      expect(config.id, 'f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c');
      expect(config.name, 'Production DB Backup');
      expect(config.backupType, 'POSTGRESQL');
      expect(config.isPostgres, true);
      expect(config.isCompressed, true);
      expect(config.retentionDays, 14);
      expect(config.environmentIsProtected, true);
    });

    test('BackupModel parses metadata, size, duration, and checksum', () {
      final json = {
        'id': 'b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'environment_id': 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'server_id': '9f0e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
        'backup_config_id': 'f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c',
        'backup_type': 'POSTGRESQL',
        'status': 'SUCCESS',
        'file_name': 'postgresql_production_db_2026-09-29_10-00-00.sql.gz',
        'file_path': '/var/backups/postgresql/postgresql_production_db_2026-09-29_10-00-00.sql.gz',
        'file_size_bytes': 10485760,
        'checksum': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        'started_at': '2026-09-29T10:00:00Z',
        'finished_at': '2026-09-29T10:01:30Z',
        'created_at': '2026-09-29T10:00:00Z',
        'backup_config_name': 'Production DB Backup',
        'environment_name': 'Production',
        'server_name': 'prod-01',
      };

      final backup = BackupModel.fromJson(json);
      expect(backup.id, 'b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e');
      expect(backup.status, 'SUCCESS');
      expect(backup.isSuccess, true);
      expect(backup.formattedFileSize, '10.0 MB');
      expect(backup.checksumSnippet, 'e3b0c442...b855');
      expect(backup.durationFormatted, '1m 30s');
    });

    test('BackupLogsModel & VerifyResultModel parse properly', () {
      final logsJson = {
        'backup_id': 'b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e',
        'status': 'RUNNING',
        'lines_returned': 2,
        'entries': [
          {
            'sequence': 1,
            'timestamp': '2026-09-29T10:00:00Z',
            'level': 'INFO',
            'message': 'Starting PostgreSQL backup',
          },
          {
            'sequence': 2,
            'timestamp': '2026-09-29T10:00:05Z',
            'level': 'ERROR',
            'message': 'Dump error notice',
          }
        ],
      };

      final logs = BackupLogsModel.fromJson(logsJson);
      expect(logs.backupId, 'b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e');
      expect(logs.entries.length, 2);
      expect(logs.entries.first.isInfo, true);
      expect(logs.entries.last.isError, true);

      final verifyJson = {
        'backup_id': 'b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e',
        'verified': true,
        'checksum': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        'verified_at': '2026-09-29T10:05:00Z',
        'message': 'Verifikasi berhasil. Checksum SHA-256 cocok.',
      };

      final verify = BackupVerifyResultModel.fromJson(verifyJson);
      expect(verify.verified, true);
      expect(verify.checksum, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
    });
  });

  group('Alert & Notification Models JSON serialization', () {
    test('AlertRuleModel parses accurately with condition formatting', () {
      final json = {
        'id': 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'name': 'High CPU Alert Rule',
        'description': 'Trigger alert when CPU > 90%',
        'metric_type': 'CPU_USAGE',
        'operator': 'GREATER_THAN',
        'threshold': 90.0,
        'duration_seconds': 300,
        'severity': 'CRITICAL',
        'is_enabled': true,
        'created_at': '2026-09-29T10:00:00Z',
      };

      final rule = AlertRuleModel.fromJson(json);
      expect(rule.id, 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d');
      expect(rule.name, 'High CPU Alert Rule');
      expect(rule.metricTypeFormatted, 'CPU Usage');
      expect(rule.operatorSymbol, '>');
      expect(rule.conditionText, '> 90%');
      expect(rule.durationFormatted, '5 mnt');
      expect(rule.isEnabled, true);
    });

    test('AlertModel & AlertEventModel parse accurately', () {
      final json = {
        'id': 'e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b',
        'workspace_id': 'c7b5a190-3204-4edb-b483-1e440b8438bf',
        'alert_rule_id': 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
        'status': 'FIRING',
        'severity': 'CRITICAL',
        'title': 'High CPU Usage on prod-01',
        'message': 'CPU usage reached 94.5%',
        'current_value': 94.5,
        'threshold_value': 90.0,
        'triggered_at': '2026-09-29T10:00:00Z',
        'events': [
          {
            'id': 'ev-1',
            'alert_id': 'e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b',
            'event_type': 'TRIGGERED',
            'message': 'Alert rule condition met',
            'created_at': '2026-09-29T10:00:00Z',
          }
        ]
      };

      final alert = AlertModel.fromJson(json);
      expect(alert.id, 'e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b');
      expect(alert.isFiring, true);
      expect(alert.isCritical, true);
      expect(alert.currentValue, 94.5);
      expect(alert.events?.length, 1);
      expect(alert.events?.first.eventType, 'TRIGGERED');
    });

    test('NotificationModel & Preferences parse accurately', () {
      final notifJson = {
        'id': 'notif-1',
        'user_id': 'u1',
        'workspace_id': 'w1',
        'title': 'High CPU Alert',
        'message': 'Server prod-01 CPU > 90%',
        'severity': 'CRITICAL',
        'is_read': false,
        'created_at': '2026-09-29T10:00:00Z',
      };

      final notif = NotificationModel.fromJson(notifJson);
      expect(notif.id, 'notif-1');
      expect(notif.isRead, false);
      expect(notif.isCritical, true);

      final prefJson = {
        'id': 'pref-1',
        'user_id': 'u1',
        'workspace_id': 'w1',
        'in_app_enabled': true,
        'email_enabled': true,
        'minimum_severity': 'WARNING',
      };

      final pref = NotificationPreferenceModel.fromJson(prefJson);
      expect(pref.inAppEnabled, true);
      expect(pref.emailEnabled, true);
      expect(pref.minimumSeverity, 'WARNING');

      final count = UnreadNotificationCountModel.fromJson({'unread_count': 5});
      expect(count.unreadCount, 5);
    });
  });

  group('AuditLogModel JSON serialization', () {
    test('fromJson correctly parses AuditLog and AuditLogListResponse', () {
      final json = {
        'id': 'audit-uuid-1',
        'workspace_id': 'ws-uuid-1',
        'user_id': 'user-uuid-1',
        'user': {
          'id': 'user-uuid-1',
          'name': 'Audit Admin',
          'email': 'admin@devops.hub',
        },
        'action': 'SERVICE_RESTARTED',
        'resource_type': 'service',
        'resource_id': 'nginx.service',
        'status': 'SUCCESS',
        'ip_address': '192.168.1.10',
        'user_agent': 'FlutterMobile/1.0',
        'metadata': {
          'service': 'nginx.service',
          'password': '********',
        },
        'created_at': '2026-09-29T10:00:00Z',
      };

      final log = AuditLogModel.fromJson(json);
      expect(log.id, 'audit-uuid-1');
      expect(log.action, 'SERVICE_RESTARTED');
      expect(log.status, 'SUCCESS');
      expect(log.user?.name, 'Audit Admin');
      expect(log.metadata?['password'], '********');

      final listJson = {
        'items': [json],
        'total': 1,
        'limit': 50,
        'offset': 0,
      };

      final listResp = AuditLogListResponseModel.fromJson(listJson);
      expect(listResp.total, 1);
      expect(listResp.items.length, 1);
      expect(listResp.items.first.action, 'SERVICE_RESTARTED');
    });
  });
}


