import 'package:get/get.dart';
import '../core/network/api_client.dart';
import '../core/storage/secure_storage_service.dart';
import '../data/services/auth_service.dart';
import '../data/services/workspace_service.dart';
import '../modules/auth/controllers/auth_controller.dart';
import '../modules/workspace/controllers/workspace_controller.dart';

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

    // Global Auth Controller
    Get.put<AuthController>(
      AuthController(authService: authService),
      permanent: true,
    );

    // Workspace Controller
    Get.lazyPut<WorkspaceController>(
      () => WorkspaceController(
        workspaceService: workspaceService,
        secureStorage: secureStorage,
      ),
      fenix: true,
    );
  }
}
