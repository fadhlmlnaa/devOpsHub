import 'package:flutter_test/flutter_test.dart';
import 'package:devops_hub/main.dart';

void main() {
  testWidgets('Initial screen renders DevOps Platform and status',
      (WidgetTester tester) async {
    await tester.pumpWidget(const DevOpsPlatformApp());

    expect(find.text('DevOps Platform'), findsAtLeastNWidgets(1));
    expect(find.text('Not Connected'), findsOneWidget);
  });
}
