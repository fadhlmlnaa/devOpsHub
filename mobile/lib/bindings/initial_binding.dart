import 'package:get/get.dart';
import '../core/network/api_client.dart';
import '../core/storage/secure_storage_service.dart';
import '../data/services/auth_service.dart';
import '../data/services/workspace_service.dart';
import '../data/services/environment_service.dart';
import '../data/services/server_service.dart';
import '../data/services/service_service.dart';
import '../data/services/log_service.dart';
import '../data/services/docker_service.dart';
import '../data/services/deployment_service.dart';
import '../data/services/backup_service.dart';
import '../data/services/alert_service.dart';
import '../data/services/audit_service.dart';
import '../data/services/agent_service.dart';
import '../modules/auth/controllers/auth_controller.dart';
import '../modules/workspace/controllers/workspace_controller.dart';
import '../modules/environment/controllers/environment_controller.dart';
import '../modules/server/controllers/server_controller.dart';
import '../modules/service/controllers/service_controller.dart';
import '../modules/log/controllers/log_controller.dart';
import '../modules/docker/controllers/docker_controller.dart';
import '../modules/docker/controllers/docker_compose_controller.dart';
import '../modules/alerts/controllers/alert_controller.dart';
import '../modules/alerts/controllers/alert_rule_controller.dart';
import '../modules/alerts/controllers/notification_controller.dart';

class InitialBinding extends Bindings {
  @override
  void dependencies() {
    // Core Services
    final secureStorage = SecureStorageService();
    Get.put<SecureStorageService>(secureStorage, permanent: true);

    final apiClient = ApiClient(secureStorage: secureStorage);
    Get.put<ApiClient>(apiClient, permanent: true);

    // Data Services
    final authService = AuthService(apiClient: apiClient, secureStorage: secureStorage);
    Get.put<AuthService>(authService, permanent: true);

    final workspaceService = WorkspaceService(apiClient: apiClient);
    Get.put<WorkspaceService>(workspaceService, permanent: true);

    final environmentService = EnvironmentService(apiClient: apiClient);
    Get.put<EnvironmentService>(environmentService, permanent: true);

    final serverService = ServerService(apiClient: apiClient);
    Get.put<ServerService>(serverService, permanent: true);

    final serviceService = ServiceService(apiClient: apiClient);
    Get.put<ServiceService>(serviceService, permanent: true);

    final logService = LogService(apiClient: apiClient);
    Get.put<LogService>(logService, permanent: true);

    final dockerService = DockerService(apiClient: apiClient);
    Get.put<DockerService>(dockerService, permanent: true);

    final deploymentService = DeploymentService(apiClient: apiClient);
    Get.put<DeploymentService>(deploymentService, permanent: true);

    final backupService = BackupService(apiClient: apiClient);
    Get.put<BackupService>(backupService, permanent: true);

    final alertService = AlertService(apiClient: apiClient);
    Get.put<AlertService>(alertService, permanent: true);

    final auditService = AuditService(apiClient: apiClient);
    Get.put<AuditService>(auditService, permanent: true);

    final agentService = AgentService(apiClient: apiClient);
    Get.put<AgentService>(agentService, permanent: true);

    // Global Auth Controller
    Get.put<AuthController>(
      AuthController(authService: authService),
      permanent: true,
    );

    // Workspace, Environment, Server, Service, Log, Docker, Alert & Notification Controllers
    Get.lazyPut<WorkspaceController>(
      () => WorkspaceController(
        workspaceService: workspaceService,
        secureStorage: secureStorage,
      ),
      fenix: true,
    );

    Get.lazyPut<EnvironmentController>(
      () => EnvironmentController(
        environmentService: environmentService,
      ),
      fenix: true,
    );

    Get.lazyPut<ServerController>(
      () => ServerController(
        serverService: serverService,
        agentService: agentService,
      ),
      fenix: true,
    );

    Get.lazyPut<ServiceController>(
      () => ServiceController(
        serviceService: serviceService,
      ),
      fenix: true,
    );

    Get.lazyPut<LogController>(
      () => LogController(
        logService: logService,
      ),
      fenix: true,
    );

    Get.lazyPut<DockerController>(
      () => DockerController(
        dockerService: dockerService,
      ),
      fenix: true,
    );

    Get.lazyPut<DockerComposeController>(
      () => DockerComposeController(
        dockerService: dockerService,
      ),
      fenix: true,
    );

    Get.lazyPut<AlertController>(
      () => AlertController(
        alertService: alertService,
      ),
      fenix: true,
    );

    Get.lazyPut<AlertRuleController>(
      () => AlertRuleController(
        alertService: alertService,
      ),
      fenix: true,
    );

    Get.lazyPut<NotificationController>(
      () => NotificationController(
        alertService: alertService,
      ),
      fenix: true,
    );
  }
}

