import 'package:get/get.dart';
import '../core/network/api_client.dart';
import '../core/storage/secure_storage_service.dart';
import '../data/services/auth_service.dart';
import '../data/services/workspace_service.dart';
import '../data/services/environment_service.dart';
import '../data/services/server_service.dart';
import '../data/services/service_service.dart';
import '../modules/auth/controllers/auth_controller.dart';
import '../modules/workspace/controllers/workspace_controller.dart';
import '../modules/environment/controllers/environment_controller.dart';
import '../modules/server/controllers/server_controller.dart';
import '../modules/service/controllers/service_controller.dart';

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

    // Global Auth Controller
    Get.put<AuthController>(
      AuthController(authService: authService),
      permanent: true,
    );

    // Workspace, Environment, Server & Service Controllers
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
      ),
      fenix: true,
    );

    Get.lazyPut<ServiceController>(
      () => ServiceController(
        serviceService: serviceService,
      ),
      fenix: true,
    );
  }
}
