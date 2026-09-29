import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:devops_hub/core/widgets/app_button.dart';
import 'package:devops_hub/core/widgets/app_text_field.dart';
import 'package:devops_hub/core/widgets/app_status_badge.dart';
import 'package:devops_hub/core/widgets/app_card.dart';

void main() {
  testWidgets('AppButton renders text and triggers callback', (WidgetTester tester) async {
    bool tapped = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AppButton(
            text: 'Submit Action',
            onPressed: () => tapped = true,
          ),
        ),
      ),
    );

    expect(find.text('Submit Action'), findsOneWidget);
    await tester.tap(find.text('Submit Action'));
    expect(tapped, isTrue);
  });

  testWidgets('AppButton shows loading indicator when isLoading is true',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: AppButton(
            text: 'Submit Action',
            isLoading: true,
          ),
        ),
      ),
    );

    expect(find.text('Memproses...'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('AppTextField displays label and hint text', (WidgetTester tester) async {
    final controller = TextEditingController();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AppTextField(
            label: 'User Email',
            hint: 'email@example.com',
            controller: controller,
          ),
        ),
      ),
    );

    expect(find.text('User Email'), findsOneWidget);
    expect(find.text('email@example.com'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField), 'test@domain.com');
    expect(controller.text, 'test@domain.com');
  });

  testWidgets('AppStatusBadge.role renders role badge correctly', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Row(
            children: [
              AppStatusBadge.role('OWNER'),
              AppStatusBadge.role('DEVELOPER'),
            ],
          ),
        ),
      ),
    );

    expect(find.text('OWNER'), findsOneWidget);
    expect(find.text('DEVELOPER'), findsOneWidget);
  });

  testWidgets('AppCard responds to tap event', (WidgetTester tester) async {
    bool tapped = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AppCard(
            onTap: () => tapped = true,
            child: const Text('Card Content'),
          ),
        ),
      ),
    );

    expect(find.text('Card Content'), findsOneWidget);
    await tester.tap(find.text('Card Content'));
    expect(tapped, isTrue);
  });
}
