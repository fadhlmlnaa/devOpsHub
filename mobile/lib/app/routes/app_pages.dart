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
import '../../modules/server/views/add_server_view.dart';
import '../../modules/server/views/server_detail_view.dart';
import '../../modules/service/views/service_list_view.dart';
import '../../modules/log/views/service_log_view.dart';
import '../../modules/docker/views/docker_dashboard_view.dart';
import '../../modules/docker/views/container_detail_view.dart';
import '../../modules/deployment/views/deployment_dashboard_view.dart';
import '../../modules/backup/views/backup_dashboard_view.dart';
import '../../modules/alerts/views/alert_dashboard_view.dart';
import '../../modules/alerts/views/notification_list_view.dart';
import '../../data/services/audit_service.dart';
import '../../modules/audit/controllers/audit_controller.dart';
import '../../modules/audit/views/audit_log_list_view.dart';
import '../../modules/terminal/views/server_terminal_view.dart';
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
    GetPage(
      name: AppRoutes.addServer,
      page: () => const AddServerView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.serverDetail,
      page: () => const ServerDetailView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.serverTerminal,
      page: () => const ServerTerminalView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.services,
      page: () => const ServiceListView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.logs,
      page: () => const ServiceLogView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.docker,
      page: () => const DockerDashboardView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.containerDetail,
      page: () => const ContainerDetailView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.deployments,
      page: () => const DeploymentDashboardView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.backups,
      page: () => const BackupDashboardView(),
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.alerts,
      page: () {
        final wsId = Get.parameters['id'] ?? '';
        return AlertDashboardView(workspaceId: wsId);
      },
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.notifications,
      page: () {
        final wsId = Get.parameters['id'] ?? '';
        return NotificationListView(workspaceId: wsId);
      },
      transition: Transition.rightToLeft,
    ),
    GetPage(
      name: AppRoutes.auditLogs,
      page: () => const AuditLogListView(),
      binding: BindingsBuilder(() {
        final wsId = Get.parameters['id'] ?? '';
        Get.put<AuditController>(
          AuditController(
            auditService: Get.find<AuditService>(),
            workspaceId: wsId,
          ),
        );
      }),
      transition: Transition.rightToLeft,
    ),
  ];
}



