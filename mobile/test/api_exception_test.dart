import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:devops_hub/core/network/api_exception.dart';

void main() {
  group('ApiException Tests', () {
    test('converts detail string correctly', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/auth/login'),
        response: Response(
          requestOptions: RequestOptions(path: '/auth/login'),
          statusCode: 401,
          data: {'detail': 'Invalid email or password'},
        ),
      );

      final apiException = ApiException.fromDioException(dioException);
      expect(apiException.message, 'Invalid email or password');
      expect(apiException.statusCode, 401);
    });

    test('converts detail list of validation errors correctly', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/auth/register'),
        response: Response(
          requestOptions: RequestOptions(path: '/auth/register'),
          statusCode: 422,
          data: {
            'detail': [
              {'msg': 'Password must be at least 8 characters long'}
            ]
          },
        ),
      );

      final apiException = ApiException.fromDioException(dioException);
      expect(apiException.message, 'Password must be at least 8 characters long');
      expect(apiException.statusCode, 422);
    });

    test('handles status code default messages when no detail field', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/workspaces'),
        response: Response(
          requestOptions: RequestOptions(path: '/workspaces'),
          statusCode: 403,
          data: {},
        ),
      );

      final apiException = ApiException.fromDioException(dioException);
      expect(apiException.message, "Anda tidak memiliki akses ke resource ini.");
    });

    test('handles connection timeout error gracefully', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/workspaces'),
        type: DioExceptionType.connectionTimeout,
      );

      final apiException = ApiException.fromDioException(dioException);
      expect(apiException.message.contains('batas waktu'), isTrue);
    });
  });
}
