import 'package:flutter_test/flutter_test.dart';
import 'package:devops_hub/data/models/user_model.dart';
import 'package:devops_hub/data/models/auth_token_model.dart';
import 'package:devops_hub/data/models/workspace_model.dart';
import 'package:devops_hub/data/models/workspace_member_model.dart';

void main() {
  group('UserModel JSON serialization', () {
    test('fromJson creates valid UserModel', () {
      final json = {
        'id': 1,
        'email': 'fadhil@example.com',
        'name': 'Fadhil Maulana',
        'is_active': true,
        'created_at': '2026-09-29T10:00:00Z',
        'updated_at': '2026-09-29T10:00:00Z',
      };

      final user = UserModel.fromJson(json);
      expect(user.id, 1);
      expect(user.email, 'fadhil@example.com');
      expect(user.name, 'Fadhil Maulana');
      expect(user.isActive, true);
      expect(user.createdAt, isNotNull);
    });

    test('toJson produces correct Map', () {
      final user = UserModel(
        id: 2,
        email: 'user@test.com',
        name: 'Test User',
      );
      final map = user.toJson();
      expect(map['id'], 2);
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
          'id': 1,
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
    });
  });

  group('WorkspaceModel JSON serialization', () {
    test('fromJson parses workspace details and user role', () {
      final json = {
        'id': 10,
        'name': 'PT Bintang',
        'description': 'Main production workspace',
        'timezone': 'Asia/Jakarta',
        'role': 'OWNER',
        'created_at': '2026-09-29T10:00:00Z',
      };

      final ws = WorkspaceModel.fromJson(json);
      expect(ws.id, 10);
      expect(ws.name, 'PT Bintang');
      expect(ws.description, 'Main production workspace');
      expect(ws.timezone, 'Asia/Jakarta');
      expect(ws.role, 'OWNER');
    });
  });

  group('WorkspaceMemberModel JSON serialization', () {
    test('fromJson parses member info correctly', () {
      final json = {
        'id': 1,
        'user_id': 2,
        'role': 'DEVELOPER',
        'user_email': 'dev@example.com',
        'user_name': 'Developer One',
      };

      final member = WorkspaceMemberModel.fromJson(json);
      expect(member.id, 1);
      expect(member.userId, 2);
      expect(member.role, 'DEVELOPER');
      expect(member.userEmail, 'dev@example.com');
    });
  });
}
