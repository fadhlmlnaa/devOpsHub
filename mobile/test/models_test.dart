import 'package:flutter_test/flutter_test.dart';
import 'package:devops_hub/data/models/user_model.dart';
import 'package:devops_hub/data/models/auth_token_model.dart';
import 'package:devops_hub/data/models/workspace_model.dart';
import 'package:devops_hub/data/models/workspace_member_model.dart';

import 'package:devops_hub/data/models/environment_model.dart';
import 'package:devops_hub/data/models/server_model.dart';
import 'package:devops_hub/data/models/connection_test_model.dart';
import 'package:devops_hub/data/models/monitoring_metrics_model.dart';
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
}
