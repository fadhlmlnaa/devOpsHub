import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/storage/secure_storage_service.dart';
import '../../../data/models/workspace_model.dart';
import '../../../data/services/workspace_service.dart';

class WorkspaceController extends GetxController {
  final WorkspaceService workspaceService;
  final SecureStorageService secureStorage;

  final RxBool isLoading = false.obs;
  final RxBool isCreating = false.obs;
  final RxList<WorkspaceModel> workspaces = <WorkspaceModel>[].obs;
  final Rxn<WorkspaceModel> selectedWorkspace = Rxn<WorkspaceModel>();
  final RxnString errorMessage = RxnString();

  WorkspaceController({
    required this.workspaceService,
    required this.secureStorage,
  });

  @override
  void onInit() {
    super.onInit();
    loadWorkspaces();
  }

  Future<void> loadWorkspaces() async {
    try {
      isLoading.value = true;
      errorMessage.value = null;

      final list = await workspaceService.getWorkspaces();
      workspaces.assignAll(list);

      // Restore selected workspace if stored in client state
      final savedWsId = await secureStorage.getSelectedWorkspaceId();
      if (savedWsId != null && list.isNotEmpty) {
        final match = list.firstWhereOrNull((w) => w.id.toString() == savedWsId);
        if (match != null) {
          selectedWorkspace.value = match;
        }
      }
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (_) {
      errorMessage.value = 'Gagal memuat daftar workspace.';
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> refreshWorkspaces() async {
    await loadWorkspaces();
  }

  void selectWorkspace(WorkspaceModel workspace) {
    selectedWorkspace.value = workspace;
    secureStorage.saveSelectedWorkspaceId(workspace.id.toString());
    Get.toNamed('/workspaces/${workspace.id}');
  }

  Future<bool> createWorkspace({
    required String name,
    String? description,
    String timezone = 'Asia/Jakarta',
  }) async {
    try {
      isCreating.value = true;
      errorMessage.value = null;

      final newWs = await workspaceService.createWorkspace(
        name: name,
        description: description,
        timezone: timezone,
      );

      // Refresh list
      await loadWorkspaces();

      // Select created workspace
      selectWorkspace(newWs);

      Get.snackbar(
        'Workspace Dibuat',
        'Workspace "${newWs.name}" berhasil dibuat sebagai OWNER.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      errorMessage.value = e.message;
      Get.snackbar(
        'Gagal Membuat Workspace',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } catch (_) {
      errorMessage.value = 'Gagal membuat workspace baru.';
      return false;
    } finally {
      isCreating.value = false;
    }
  }
}
