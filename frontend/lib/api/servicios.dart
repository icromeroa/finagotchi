import 'api_client.dart';

/// Instancia compartida del cliente de la API.
///
/// Se mantiene una sola para que el token de acceso survived a los cambios
/// de pantalla. Para probar contra otro backend se compila con:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.7:5000/api/v1
final ApiClient api = ApiClient();
