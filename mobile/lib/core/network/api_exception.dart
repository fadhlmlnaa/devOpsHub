import 'package:dio/dio.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic data;

  ApiException({
    required this.message,
    this.statusCode,
    this.data,
  });

  factory ApiException.fromDioException(DioException error) {
    String message = 'Terjadi kesalahan koneksi ke server.';
    final statusCode = error.response?.statusCode;
    final responseData = error.response?.data;

    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      message = 'Koneksi batas waktu (timeout). Silakan periksa jaringan Anda.';
    } else if (error.type == DioExceptionType.connectionError) {
      message = 'Gagal terhubung ke server backend. Pastikan server aktif.';
    } else if (error.response != null) {
      if (responseData is Map && responseData.containsKey('detail')) {
        final detail = responseData['detail'];
        if (detail is String) {
          message = detail;
        } else if (detail is List && detail.isNotEmpty) {
          final firstError = detail.first;
          if (firstError is Map && firstError.containsKey('msg')) {
            message = firstError['msg'].toString();
          } else {
            message = detail.toString();
          }
        }
      } else {
        switch (statusCode) {
          case 400:
            message = 'Permintaan tidak valid.';
            break;
          case 401:
            message = 'Sesi berakhir atau kredensial salah.';
            break;
          case 403:
            message = 'Anda tidak memiliki akses ke resource ini.';
            break;
          case 404:
            message = 'Data tidak ditemukan.';
            break;
          case 409:
            message = 'Data sudah ada atau terjadi konflik data.';
            break;
          case 422:
            message = 'Input data tidak valid.';
            break;
          case 500:
            message = 'Terjadi kesalahan pada server (Internal Server Error).';
            break;
          default:
            message = 'Terjadi kesalahan dengan kode status: $statusCode';
        }
      }
    }

    return ApiException(
      message: message,
      statusCode: statusCode,
      data: responseData,
    );
  }

  @override
  String toString() => message;
}
