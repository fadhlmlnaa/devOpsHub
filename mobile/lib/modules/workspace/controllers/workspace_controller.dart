import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/storage/secure_storage_service.dart';
import '../../../data/models/workspace_member_model.dart';
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

  // Member Management State
  final RxList<WorkspaceMemberModel> members = <WorkspaceMemberModel>[].obs;
  final RxBool isLoadingMembers = false.obs;
  final RxBool isActionInProgress = false.obs;

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
          loadMembers(match.id);
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
    loadMembers(workspace.id);
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

  // ==================== WORKSPACE MEMBERS ====================

  Future<void> loadMembers(String workspaceId) async {
    try {
      isLoadingMembers.value = true;
      final list = await workspaceService.getWorkspaceMembers(workspaceId);
      members.assignAll(list);
    } on ApiException catch (e) {
      Get.snackbar('Error', e.message, snackPosition: SnackPosition.BOTTOM);
    } catch (_) {
      // silently handle or log
    } finally {
      isLoadingMembers.value = false;
    }
  }

  Future<bool> addMember({
    required String workspaceId,
    required String email,
    required String role,
  }) async {
    try {
      isActionInProgress.value = true;
      final newMember = await workspaceService.addWorkspaceMember(
        workspaceId,
        email: email,
        role: role,
      );
      members.add(newMember);
      Get.snackbar(
        'Berhasil',
        'Pengguna $email berhasil ditambahkan sebagai $role.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Menambah Member', e.message, snackPosition: SnackPosition.BOTTOM);
      return false;
    } catch (_) {
      Get.snackbar('Gagal', 'Terjadi kesalahan saat menambahkan anggota.', snackPosition: SnackPosition.BOTTOM);
      return false;
    } finally {
      isActionInProgress.value = false;
    }
  }

  Future<bool> updateMemberRole({
    required String workspaceId,
    required String userId,
    required String newRole,
  }) async {
    try {
      isActionInProgress.value = true;
      final updated = await workspaceService.updateWorkspaceMemberRole(
        workspaceId,
        userId,
        role: newRole,
      );
      final index = members.indexWhere((m) => m.userId == userId || m.id == updated.id);
      if (index != -1) {
        members[index] = updated;
      } else {
        await loadMembers(workspaceId);
      }
      Get.snackbar(
        'Role Diperbarui',
        'Role anggota berhasil diubah menjadi $newRole.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Mengubah Role', e.message, snackPosition: SnackPosition.BOTTOM);
      return false;
    } catch (_) {
      Get.snackbar('Gagal', 'Terjadi kesalahan saat memperbarui role anggota.', snackPosition: SnackPosition.BOTTOM);
      return false;
    } finally {
      isActionInProgress.value = false;
    }
  }

  Future<bool> removeMember({
    required String workspaceId,
    required String userId,
    String? name,
  }) async {
    try {
      isActionInProgress.value = true;
      await workspaceService.removeWorkspaceMember(workspaceId, userId);
      members.removeWhere((m) => m.userId == userId);
      Get.snackbar(
        'Anggota Dihapus',
        'Anggota ${name ?? ""} berhasil dikeluarkan dari workspace.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Menghapus Member', e.message, snackPosition: SnackPosition.BOTTOM);
      return false;
    } catch (_) {
      Get.snackbar('Gagal', 'Terjadi kesalahan saat menghapus anggota.', snackPosition: SnackPosition.BOTTOM);
      return false;
    } finally {
      isActionInProgress.value = false;
    }
  }

  Future<bool> leaveWorkspace(String workspaceId) async {
    try {
      isActionInProgress.value = true;
      await workspaceService.leaveWorkspace(workspaceId);
      await loadWorkspaces();
      Get.offAllNamed('/workspaces');
      Get.snackbar(
        'Keluar Workspace',
        'Anda telah keluar dari workspace.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return true;
    } on ApiException catch (e) {
      Get.snackbar('Gagal Keluar Workspace', e.message, snackPosition: SnackPosition.BOTTOM);
      return false;
    } catch (_) {
      Get.snackbar('Gagal', 'Terjadi kesalahan saat keluar dari workspace.', snackPosition: SnackPosition.BOTTOM);
      return false;
    } finally {
      isActionInProgress.value = false;
    }
  }
}

