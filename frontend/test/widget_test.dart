import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/screens/login_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  /// El boton esta al final de una columna que se puede desplazar, asi que
  /// hay que traerlo a la vista antes de pulsarlo.
  Future<void> pulsarEntrar(WidgetTester tester) async {
    final boton = find.text('Entrar a mi Finagotchi');
    await tester.ensureVisible(boton);
    await tester.pumpAndSettle();
    await tester.tap(boton);
    await tester.pumpAndSettle();
  }

  testWidgets('la pantalla de acceso se monta', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: LoginScreen()));
    await tester.pump();

    expect(find.text('Ingresa a tu cuenta'), findsOneWidget);
    expect(find.text('Entrar a mi Finagotchi'), findsOneWidget);
  });

  testWidgets('pide correo y contraseña validos', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: LoginScreen()));
    await tester.pump();

    await pulsarEntrar(tester);

    expect(find.text('Usa un correo válido ej: name@gmail.com'), findsOneWidget);
    expect(find.text('Ingresa tu contraseña'), findsOneWidget);
  });

  testWidgets('acepta un correo con formato correcto',
      (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: LoginScreen()));
    await tester.pump();

    await tester.enterText(
      find.byType(TextField).first,
      'ana@example.com',
    );
    await tester.pump();
    await pulsarEntrar(tester);

    expect(find.text('Usa un correo válido ej: name@gmail.com'), findsNothing);
  });
}
