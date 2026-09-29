import 'package:get/get.dart';
import '../../../core/network/api_exception.dart';
import '../../../data/models/user_model.dart';
import '../../../data/services/auth_service.dart';

class AuthController extends GetxController {
  final AuthService authService;

  final RxBool isLoading = false.obs;
  final Rxn<UserModel> currentUser = Rxn<UserModel>();
  final RxnString errorMessage = RxnString();
  final RxBool isPasswordVisible = false.obs;

  bool get isAuthenticated => currentUser.value != null;

  AuthController({required this.authService});

  void togglePasswordVisibility() {
    isPasswordVisible.value = !isPasswordVisible.value;
  }

  void setUser(UserModel user) {
    currentUser.value = user;
    errorMessage.value = null;
  }

  Future<bool> login({
    required String email,
    required String password,
  }) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;

      final tokenData = await authService.login(
        email: email,
        password: password,
      );

      if (tokenData.user != null) {
        currentUser.value = tokenData.user;
      } else {
        // Fetch user info via /auth/me
        final user = await authService.getMe();
        currentUser.value = user;
      }

      Get.offAllNamed('/workspaces');
      return true;
    } on ApiException catch (e) {
      errorMessage.value = e.message;
      return false;
    } catch (e) {
      errorMessage.value = 'Gagal melakukan login. Silakan periksa koneksi Anda.';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  Future<bool> register({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      isLoading.value = true;
      errorMessage.value = null;

      await authService.register(
        name: name,
        email: email,
        password: password,
      );

      // Automatically login after successful registration
      return await login(
        email: email,
        password: password,
      );
    } on ApiException catch (e) {
      errorMessage.value = e.message;
      return false;
    } catch (e) {
      errorMessage.value = 'Gagal melakukan pendaftaran akun: ${e.toString()}';
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> logout() async {
    try {
      isLoading.value = true;
      await authService.logout();
    } finally {
      currentUser.value = null;
      errorMessage.value = null;
      isLoading.value = false;
      Get.offAllNamed('/auth/login');
    }
  }

  Future<void> checkSession() async {
    try {
      final isAuth = await authService.isAuthenticated();
      if (!isAuth) {
        currentUser.value = null;
        return;
      }
      final user = await authService.getMe();
      currentUser.value = user;
    } catch (_) {
      currentUser.value = null;
    }
  }
}
