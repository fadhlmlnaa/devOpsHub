import 'package:get/get.dart';
import '../../bindings/auth_binding.dart';
import '../../bindings/workspace_binding.dart';
import '../../data/services/auth_service.dart';
import '../../modules/auth/views/login_view.dart';
import '../../modules/auth/views/register_view.dart';
import '../../modules/splash/controllers/splash_controller.dart';
import '../../modules/splash/views/splash_view.dart';
import '../../modules/workspace/views/workspace_home_view.dart';
import '../../modules/workspace/views/workspace_list_view.dart';
import 'app_routes.dart';

class AppPages {
  AppPages._();

  static const initial = AppRoutes.splash;

  static final routes = [
    GetPage(
      name: AppRoutes.splash,
      page: () => const SplashView(),
      binding: BindingsBuilder(() {
        Get.put<SplashController>(
          SplashController(authService: Get.find<AuthService>()),
        );
      }),
    ),
    GetPage(
      name: AppRoutes.login,
      page: () => const LoginView(),
      binding: AuthBinding(),
      transition: Transition.fadeIn,
    ),
    GetPage(
      name: AppRoutes.register,
      page: () => const RegisterView(),
      binding: AuthBinding(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.workspaces,
      page: () => const WorkspaceListView(),
      binding: WorkspaceBinding(),
      transition: Transition.fadeIn,
    ),
    GetPage(
      name: AppRoutes.workspaceHome,
      page: () => const WorkspaceHomeView(),
      binding: WorkspaceBinding(),
      transition: Transition.rightToLeft,
    ),
  ];
}
