import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'app/routes/app_pages.dart';
import 'app/theme/app_colors.dart';
import 'app/theme/app_theme.dart';
import 'bindings/initial_binding.dart';

import 'core/constants/app_constants.dart';
import 'core/storage/secure_storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load saved custom base URL if configured by user
  try {
    final storage = SecureStorageService();
    final customUrl = await storage.getCustomBaseUrl();
    if (customUrl != null && customUrl.isNotEmpty) {
      AppConstants.baseUrl = customUrl;
    }
  } catch (_) {}

  // Set system UI overlay style matching dark teal theme
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: AppColors.background,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  runApp(const DevOpsHubApp());
}

class DevOpsHubApp extends StatelessWidget {
  const DevOpsHubApp({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'DevOpsHub',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.dark,
      initialBinding: InitialBinding(),
      initialRoute: AppPages.initial,
      getPages: AppPages.routes,
      defaultTransition: Transition.fade,
    );
  }
}
