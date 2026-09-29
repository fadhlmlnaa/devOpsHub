import 'package:get/get.dart';
import '../core/storage/secure_storage_service.dart';
import '../data/services/workspace_service.dart';
import '../modules/workspace/controllers/workspace_controller.dart';

class WorkspaceBinding extends Bindings {
  @override
  void dependencies() {
    if (!Get.isRegistered<WorkspaceController>()) {
      Get.lazyPut<WorkspaceController>(
        () => WorkspaceController(
          workspaceService: Get.find<WorkspaceService>(),
          secureStorage: Get.find<SecureStorageService>(),
        ),
      );
    }
  }
}
