import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/environment_model.dart';
import '../../../data/services/environment_service.dart';

class EnvironmentController extends GetxController {
  final EnvironmentService environmentService;

  final RxBool isLoading = false.obs;
  final RxBool isCreating = false.obs;
  final RxList<EnvironmentModel> environments = <EnvironmentModel>[].obs;
  final RxnString errorMessage = RxnString();

  EnvironmentController({required this.environmentService});

  Future<void> loadEnvironments(String workspaceId) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;

      final list = await environmentService.getEnvironments(workspaceId);
      environments.assignAll(list);
    } on ApiException catch (e) {
      errorMessage.value = e.message;
    } catch (_) {
      errorMessage.value = 'Gagal memuat daftar environment.';
    } finally {
      isLoading.value = false;
    }
  }

  Future<bool> createEnvironment({
    required String workspaceId,
    required String name,
    required String key,
    String? description,
  }) async {
    try {
      isCreating.value = true;
      errorMessage.value = null;

      final newEnv = await environmentService.createEnvironment(
        workspaceId: workspaceId,
        name: name,
        key: key,
        description: description,
      );

      environments.add(newEnv);
      Get.snackbar(
        'Environment Ditambahkan',
        'Environment "${newEnv.name}" berhasil dibuat.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Menambahkan Environment',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } catch (_) {
      Get.snackbar(
        'Gagal',
        'Terjadi kesalahan saat membuat environment.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } finally {
      isCreating.value = false;
    }
  }

  Future<bool> deleteEnvironment(String workspaceId, String environmentId) async {
    try {
      isLoading.value = true;
      await environmentService.deleteEnvironment(workspaceId, environmentId);
      environments.removeWhere((e) => e.id == environmentId);
      Get.snackbar(
        'Berhasil',
        'Environment berhasil dihapus.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar(
        'Gagal Menghapus',
        e.message,
        snackPosition: SnackPosition.BOTTOM,
      );
      return false;
    } finally {
      isLoading.value = false;
    }
  }
}
