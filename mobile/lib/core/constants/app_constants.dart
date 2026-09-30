class AppConstants {
  AppConstants._();

  // Base API configuration
  // With 'adb reverse tcp:8000 tcp:8000', both Android device and desktop/web use 127.0.0.1:8000
  static String get defaultBaseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    return 'https://hebrew-median-kerry-highway.trycloudflare.com/api/v1';
  }

  static String baseUrl = defaultBaseUrl;

  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);
  static const Duration sendTimeout = Duration(seconds: 15);

  // Storage Keys
  static const String keyAccessToken = 'devops_access_token';
  static const String keyRefreshToken = 'devops_refresh_token';
  static const String keyUserEmail = 'devops_user_email';
  static const String keyUserName = 'devops_user_name';
  static const String keyUserId = 'devops_user_id';
  static const String keySelectedWorkspaceId = 'devops_selected_ws_id';
  static const String keyCustomBaseUrl = 'devops_custom_base_url';
}
