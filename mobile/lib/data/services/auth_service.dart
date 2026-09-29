import '../models/auth_token_model.dart';
import '../models/user_model.dart';
import '../../core/network/api_client.dart';
import '../../core/storage/secure_storage_service.dart';

class AuthService {
  final ApiClient apiClient;
  final SecureStorageService secureStorage;

  AuthService({
    required this.apiClient,
    required this.secureStorage,
  });

  Future<AuthTokenModel> login({
    required String email,
    required String password,
  }) async {
    final response = await apiClient.post(
      '/auth/login',
      data: {
        'email': email.trim(),
        'password': password,
      },
    );

    final authData = AuthTokenModel.fromJson(response.data as Map<String, dynamic>);

    // Save tokens securely
    await secureStorage.saveTokens(
      accessToken: authData.accessToken,
      refreshToken: authData.refreshToken,
    );

    // If user info is returned, save it
    if (authData.user != null) {
      await secureStorage.saveUserInfo(
        id: authData.user!.id.toString(),
        email: authData.user!.email,
        name: authData.user!.name,
      );
    }

    return authData;
  }

  Future<UserModel> register({
    required String name,
    required String email,
    required String password,
  }) async {
    final response = await apiClient.post(
      '/auth/register',
      data: {
        'name': name.trim(),
        'email': email.trim(),
        'password': password,
      },
    );

    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<AuthTokenModel?> refreshToken() async {
    final currentRefreshToken = await secureStorage.getRefreshToken();
    if (currentRefreshToken == null || currentRefreshToken.isEmpty) {
      return null;
    }

    final response = await apiClient.post(
      '/auth/refresh',
      data: {
        'refresh_token': currentRefreshToken,
      },
    );

    final authData = AuthTokenModel.fromJson(response.data as Map<String, dynamic>);

    await secureStorage.saveTokens(
      accessToken: authData.accessToken,
      refreshToken: authData.refreshToken,
    );

    return authData;
  }

  Future<UserModel> getMe() async {
    final response = await apiClient.get('/auth/me');
    final user = UserModel.fromJson(response.data as Map<String, dynamic>);

    await secureStorage.saveUserInfo(
      id: user.id.toString(),
      email: user.email,
      name: user.name,
    );

    return user;
  }

  Future<void> logout() async {
    try {
      final currentRefreshToken = await secureStorage.getRefreshToken();
      if (currentRefreshToken != null && currentRefreshToken.isNotEmpty) {
        await apiClient.post(
          '/auth/logout',
          data: {
            'refresh_token': currentRefreshToken,
          },
        );
      }
    } catch (_) {
      // Even if network fails, ensure local session is cleared safely
    } finally {
      await clearSession();
    }
  }

  Future<bool> isAuthenticated() async {
    final accessToken = await secureStorage.getAccessToken();
    return accessToken != null && accessToken.isNotEmpty;
  }

  Future<void> clearSession() async {
    await secureStorage.clearAll();
  }
}
