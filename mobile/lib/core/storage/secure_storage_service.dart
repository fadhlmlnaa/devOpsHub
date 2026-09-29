import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/app_constants.dart';

class SecureStorageService {
  final FlutterSecureStorage _storage;

  SecureStorageService({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
              iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
            );

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: AppConstants.keyAccessToken, value: accessToken);
    await _storage.write(key: AppConstants.keyRefreshToken, value: refreshToken);
  }

  Future<void> saveAccessToken(String accessToken) async {
    await _storage.write(key: AppConstants.keyAccessToken, value: accessToken);
  }

  Future<void> saveRefreshToken(String refreshToken) async {
    await _storage.write(key: AppConstants.keyRefreshToken, value: refreshToken);
  }

  Future<String?> getAccessToken() async {
    return await _storage.read(key: AppConstants.keyAccessToken);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: AppConstants.keyRefreshToken);
  }

  Future<void> saveUserInfo({
    required String id,
    required String email,
    required String name,
  }) async {
    await _storage.write(key: AppConstants.keyUserId, value: id);
    await _storage.write(key: AppConstants.keyUserEmail, value: email);
    await _storage.write(key: AppConstants.keyUserName, value: name);
  }

  Future<Map<String, String?>> getUserInfo() async {
    final id = await _storage.read(key: AppConstants.keyUserId);
    final email = await _storage.read(key: AppConstants.keyUserEmail);
    final name = await _storage.read(key: AppConstants.keyUserName);
    return {'id': id, 'email': email, 'name': name};
  }

  Future<void> saveSelectedWorkspaceId(String workspaceId) async {
    await _storage.write(key: AppConstants.keySelectedWorkspaceId, value: workspaceId);
  }

  Future<String?> getSelectedWorkspaceId() async {
    return await _storage.read(key: AppConstants.keySelectedWorkspaceId);
  }

  Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}
