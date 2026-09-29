import 'package:get/get.dart';
import '../../../data/models/audit_log_model.dart';
import '../../../data/services/audit_service.dart';

class AuditController extends GetxController {
  final AuditService auditService;
  final String workspaceId;

  AuditController({
    required this.auditService,
    required this.workspaceId,
  });

  final RxBool isLoading = false.obs;
  final RxString errorMessage = ''.obs;
  final RxList<AuditLogModel> auditLogs = <AuditLogModel>[].obs;
  final RxInt totalCount = 0.obs;

  final RxString selectedStatus = 'ALL'.obs;
  final RxString selectedAction = ''.obs;

  @override
  void onInit() {
    super.onInit();
    fetchAuditLogs();
  }

  Future<void> fetchAuditLogs({bool refresh = false}) async {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      final res = await auditService.getWorkspaceAuditLogs(
        workspaceId,
        status: selectedStatus.value == 'ALL' ? null : selectedStatus.value,
        action: selectedAction.value.isEmpty ? null : selectedAction.value,
        limit: 50,
        offset: 0,
      );
      auditLogs.assignAll(res.items);
      totalCount.value = res.total;
    } catch (e) {
      errorMessage.value = e.toString();
    } finally {
      isLoading.value = false;
    }
  }

  void setStatusFilter(String status) {
    selectedStatus.value = status;
    fetchAuditLogs();
  }

  void setActionFilter(String action) {
    selectedAction.value = action;
    fetchAuditLogs();
  }
}
