import 'package:flutter_test/flutter_test.dart';
import 'package:devops_hub/main.dart';

void main() {
  testWidgets('DevOpsHubApp initializes and shows splash screen branding',
      (WidgetTester tester) async {
    await tester.pumpWidget(const DevOpsHubApp());
    expect(find.text('DevOpsHub'), findsOneWidget);
    expect(find.text('Unified DevOps & Infrastructure Control'), findsOneWidget);

    // Let the splash controller delay timer finish
    await tester.pump(const Duration(seconds: 1));
  });
}
