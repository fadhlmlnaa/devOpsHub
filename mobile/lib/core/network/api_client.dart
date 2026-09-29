import 'dart:async';
import 'package:dio/dio.dart';
import 'package:get/get.dart' as get_x;
import '../constants/app_constants.dart';
import '../storage/secure_storage_service.dart';
import 'api_exception.dart';

class ApiClient {
  late final Dio dio;
  final SecureStorageService secureStorage;

  // Single-flight refresh token lock
  Completer<bool>? _refreshCompleter;

  ApiClient({required this.secureStorage, Dio? customDio}) {
    dio = customDio ??
        Dio(
          BaseOptions(
            baseUrl: AppConstants.baseUrl,
            connectTimeout: AppConstants.connectTimeout,
            receiveTimeout: AppConstants.receiveTimeout,
            sendTimeout: AppConstants.sendTimeout,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
          ),
        );

    _setupInterceptors();
  }

  void _setupInterceptors() {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Attach access token if present and not an auth endpoint
          final isAuthEndpoint = options.path.contains('/auth/login') ||
              options.path.contains('/auth/register');

          if (!isAuthEndpoint) {
            final accessToken = await secureStorage.getAccessToken();
            if (accessToken != null && accessToken.isNotEmpty) {
              options.headers['Authorization'] = 'Bearer $accessToken';
            }
          }
          return handler.next(options);
        },
        onError: (DioException error, handler) async {
          final requestPath = error.requestOptions.path;
          final isAuthRefreshOrLogin = requestPath.contains('/auth/login') ||
              requestPath.contains('/auth/register') ||
              requestPath.contains('/auth/refresh');

          // Check if 401 Unauthorized and not already on auth/refresh endpoints
          if (error.response?.statusCode == 401 && !isAuthRefreshOrLogin) {
            final refreshed = await _handleTokenRefresh();

            if (refreshed) {
              // Retry original request with new token
              try {
                final newAccessToken = await secureStorage.getAccessToken();
                final opts = Options(
                  method: error.requestOptions.method,
                  headers: Map<String, dynamic>.from(error.requestOptions.headers)
                    ..['Authorization'] = 'Bearer $newAccessToken',
                );

                final response = await dio.request(
                  error.requestOptions.path,
                  data: error.requestOptions.data,
                  queryParameters: error.requestOptions.queryParameters,
                  options: opts,
                );
                return handler.resolve(response);
              } catch (retryError) {
                if (retryError is DioException) {
                  return handler.reject(retryError);
                }
                return handler.reject(error);
              }
            } else {
              // Refresh failed or session revoked -> force clear session & redirect to login
              await secureStorage.clearAll();
              if (get_x.Get.currentRoute != '/auth/login') {
                get_x.Get.offAllNamed('/auth/login');
              }
            }
          }

          return handler.next(error);
        },
      ),
    );
  }

  Future<bool> _handleTokenRefresh() async {
    // If a refresh is already in flight, wait for it
    if (_refreshCompleter != null) {
      return _refreshCompleter!.future;
    }

    _refreshCompleter = Completer<bool>();

    try {
      final refreshToken = await secureStorage.getRefreshToken();
      if (refreshToken == null || refreshToken.isEmpty) {
        _refreshCompleter!.complete(false);
        return false;
      }

      // Create a separate clean Dio instance to prevent infinite interceptor loops
      final refreshDio = Dio(
        BaseOptions(
          baseUrl: AppConstants.baseUrl,
          connectTimeout: AppConstants.connectTimeout,
          receiveTimeout: AppConstants.receiveTimeout,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        ),
      );

      final response = await refreshDio.post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      if (response.statusCode == 200 && response.data is Map) {
        final data = response.data as Map<String, dynamic>;
        final newAccessToken = data['access_token'] as String?;
        final newRefreshToken = data['refresh_token'] as String?;

        if (newAccessToken != null && newAccessToken.isNotEmpty) {
          await secureStorage.saveAccessToken(newAccessToken);
          // Handle refresh token rotation if returned
          if (newRefreshToken != null && newRefreshToken.isNotEmpty) {
            await secureStorage.saveRefreshToken(newRefreshToken);
          }
          _refreshCompleter!.complete(true);
          return true;
        }
      }

      _refreshCompleter!.complete(false);
      return false;
    } catch (_) {
      _refreshCompleter?.complete(false);
      return false;
    } finally {
      _refreshCompleter = null;
    }
  }

  // Generic Request Methods
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await dio.get<T>(
        path,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await dio.post<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await dio.patch<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await dio.delete<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
