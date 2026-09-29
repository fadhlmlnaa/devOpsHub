import 'package:get/get.dart';
import '../data/services/auth_service.dart';
import '../modules/auth/controllers/auth_controller.dart';

class AuthBinding extends Bindings {
  @override
  void dependencies() {
    if (!Get.isRegistered<AuthController>()) {
      Get.lazyPut<AuthController>(
        () => AuthController(authService: Get.find<AuthService>()),
      );
    }
  }
}
