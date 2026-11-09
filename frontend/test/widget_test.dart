import 'package:flutter_test/flutter_test.dart';

import 'package:frontend/main.dart';
import 'package:frontend/screens/onboarding/presentation_screen_1.dart';
import 'package:frontend/screens/onboarding/splash_screen.dart';

void main() {
  testWidgets('arranca en el splash y pasa a la presentación',
      (WidgetTester tester) async {
    await tester.pumpWidget(const FinaGotchiApp());

    expect(find.byType(SplashScreen), findsOneWidget);

    await tester.pump(const Duration(seconds: 2));
    await tester.pumpAndSettle();

    expect(find.byType(PresentationScreen1), findsOneWidget);
  });
}
