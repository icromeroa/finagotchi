import 'package:flutter/foundation.dart';

/// Dirección del backend según la plataforma.
///
/// El backend de desarrollo escucha en el puerto 5001. En el emulador de
/// Android el host del equipo se alcanza con `10.0.2.2`; en macOS, iOS,
/// escritorio y web se usa `127.0.0.1`.
///
/// Para probar desde un teléfono físico en la misma red, pásalo al compilar:
///
///     flutter run --dart-define=API_BASE_URL=http://192.168.1.22:5001/api/v1
String get apiBaseUrl {
  const override = String.fromEnvironment('API_BASE_URL');
  if (override.isNotEmpty) {
    return override;
  }
  if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:5001/api/v1';
  }
  return 'http://127.0.0.1:5001/api/v1';
}
