import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/screens/home_screen.dart';
import 'package:frontend/screens/onboarding/device_link_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('el paso de vincular el dispositivo se puede saltar',
      (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: DeviceLinkScreen()));
    await tester.pump();

    expect(find.text('Ahora no'), findsOneWidget);

    await tester.tap(find.text('Ahora no'));
    await tester.pumpAndSettle();

    // El boton debe llevar al home sin pasar por el resto del onboarding.
    expect(find.byType(HomeScreen), findsOneWidget);
  });
}
