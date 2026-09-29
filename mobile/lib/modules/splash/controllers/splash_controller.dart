import 'package:get/get.dart';
import '../../../data/services/auth_service.dart';
import '../../auth/controllers/auth_controller.dart';

class SplashController extends GetxController {
  final AuthService authService;

  SplashController({required this.authService});

  @override
  void onInit() {
    super.onInit();
    checkSession();
  }

  Future<void> checkSession() async {
    // Add small delay for smooth visual transition
    await Future.delayed(const Duration(milliseconds: 600));

    try {
      final isAuth = await authService.isAuthenticated();
      if (!isAuth) {
        Get.offAllNamed('/auth/login');
        return;
      }

      // Validate session with backend
      final user = await authService.getMe();
      
      // Update global AuthController if registered
      if (Get.isRegistered<AuthController>()) {
        Get.find<AuthController>().setUser(user);
      }

      Get.offAllNamed('/workspaces');
    } catch (_) {
      // If session is expired or invalid, reset and go to login
      await authService.clearSession();
      Get.offAllNamed('/auth/login');
    }
  }
}
