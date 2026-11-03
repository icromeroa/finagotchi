import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Error que devuelve el backend con el sobre `{"ok": false, "error": {...}}`.
class ApiError implements Exception {
  ApiError(this.codigo, this.mensaje, {this.estado = 0, this.detalles = const {}});

  final String codigo;
  final String mensaje;
  final int estado;
  final Map<String, dynamic> detalles;

  bool get esSinConexion => estado == 0;

  @override
  String toString() => mensaje;
}

/// Cliente HTTP del backend de FinaGotchi.
///
/// La direccion base se resuelve asi:
/// 1. El define `API_BASE_URL` si se paso al compilar.
/// 2. `127.0.0.1` en web y escritorio.
/// 3. `10.0.2.2` en el emulador de Android, que es como ve al host.
///
/// Con el emulador de Android:
///   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:5000/api/v1
/// Con un telefono real en la misma red, la IP del PC:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.7:5000/api/v1
class ApiClient {
  ApiClient({http.Client? cliente, String? direccionBase})
      : _http = cliente ?? http.Client(),
        direccionBase = direccionBase ?? _direccionPorDefecto();

  final http.Client _http;
  final String direccionBase;

  String? _accessToken;
  String? _refreshToken;
  bool _refrescando = false;

  static const _clavePrefijo = 'finagotchi_token_';

  String get accessToken => _accessToken ?? '';

  bool get haySesion => (_accessToken ?? '').isNotEmpty;

  static String _direccionPorDefecto() {
    const definida = String.fromEnvironment('API_BASE_URL');
    if (definida.isNotEmpty) return definida;
    if (kIsWeb) return 'http://127.0.0.1:5000/api/v1';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:5000/api/v1';
    }
    return 'http://127.0.0.1:5000/api/v1';
  }

  // ---------------------------------------------------------------- sesion

  /// Guarda la sesion en memoria y en el almacenamiento del dispositivo.
  Future<void> guardarTokens(String acceso, String refresco) async {
    _accessToken = acceso;
    _refreshToken = refresco;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('${_clavePrefijo}access', acceso);
    await prefs.setString('${_clavePrefijo}refresh', refresco);
  }

  /// Recupera una sesion guardada en una ejecucion anterior.
  Future<bool> restaurarSesion() async {
    final prefs = await SharedPreferences.getInstance();
    final acceso = prefs.getString('${_clavePrefijo}access');
    if (acceso == null || acceso.isEmpty) return false;
    _accessToken = acceso;
    _refreshToken = prefs.getString('${_clavePrefijo}refresh');
    return true;
  }

  Future<void> cerrarSesion() async {
    _accessToken = null;
    _refreshToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('${_clavePrefijo}access');
    await prefs.remove('${_clavePrefijo}refresh');
  }

  // ---------------------------------------------------------------- interno

  Map<String, String> _cabeceras({bool json = true}) => {
        if (json) 'Content-Type': 'application/json',
        if ((_accessToken ?? '').isNotEmpty)
          'Authorization': 'Bearer $_accessToken',
      };

  Uri _uri(String ruta) => Uri.parse('$direccionBase$ruta');

  /// Hace la peticion y desenvuelve el sobre del backend.
  Future<Map<String, dynamic>> _peticion(
    String metodo,
    String ruta, {
    Object? cuerpo,
    Map<String, String>? cabeceras,
    bool reintentar = true,
  }) async {
    http.Response respuesta;
    try {
      final peticion = http.Request(metodo, _uri(ruta));
      peticion.headers.addAll(cabeceras ?? _cabeceras());
      if (cuerpo != null) {
        if (cuerpo is Map) {
          peticion.body = jsonEncode(cuerpo);
        } else {
          peticion.bodyBytes = cuerpo as List<int>;
        }
      }
      respuesta = await http.Response.fromStream(
        await _http.send(peticion).timeout(const Duration(seconds: 90)),
      );
    } catch (e) {
      throw ApiError(
        'SIN_CONEXION',
        'No se pudo conectar con el backend. Revisa que este corriendo y que la '
        'direccion sea correcta.',
      );
    }

    if (respuesta.statusCode == 401 && reintentar && _refreshToken != null) {
      if (await _refrescarToken()) {
        return _peticion(metodo, ruta,
            cuerpo: cuerpo, cabeceras: cabeceras, reintentar: false);
      }
    }

    Map<String, dynamic> datos;
    try {
      datos = jsonDecode(respuesta.body) as Map<String, dynamic>;
    } catch (_) {
      throw ApiError(
        'RESPUESTA_INVALIDA',
        'El backend devolvio una respuesta que no se pudo leer.',
        estado: respuesta.statusCode,
      );
    }

    if (datos['ok'] == true) {
      final data = datos['data'];
      if (data is Map<String, dynamic>) return data;
      return {'items': data};
    }

    final error = (datos['error'] ?? {}) as Map<String, dynamic>;
    throw ApiError(
      (error['codigo'] ?? 'ERROR').toString(),
      (error['mensaje'] ?? 'Ocurrio un error.').toString(),
      estado: respuesta.statusCode,
      detalles: (error['detalles'] ?? {}) as Map<String, dynamic>,
    );
  }

  Future<bool> _refrescarToken() async {
    if (_refrescando) return false;
    _refrescando = true;
    try {
      final datos = await _peticion(
        'POST',
        '/auth/refresh',
        cuerpo: {'refresh_token': _refreshToken},
        reintentar: false,
      );
      final tokens = (datos['tokens'] ?? {}) as Map<String, dynamic>;
      await guardarTokens(
        (tokens['access_token'] ?? '').toString(),
        (tokens['refresh_token'] ?? _refreshToken ?? '').toString(),
      );
      return true;
    } catch (_) {
      await cerrarSesion();
      return false;
    } finally {
      _refrescando = false;
    }
  }

  // ------------------------------------------------------------ endpoints

  Future<Map<String, dynamic>> login(String correo, String password) async {
    final datos = await _peticion('POST', '/auth/login',
        cuerpo: {'correo': correo, 'password': password});
    final tokens = (datos['tokens'] ?? {}) as Map<String, dynamic>;
    await guardarTokens(
      (tokens['access_token'] ?? '').toString(),
      (tokens['refresh_token'] ?? '').toString(),
    );
    return datos;
  }

  Future<Map<String, dynamic>> registrar(
    String nombre,
    String correo,
    String password, {
    Map<String, dynamic> extra = const {},
  }) async {
    final datos = await _peticion('POST', '/auth/register', cuerpo: {
      'nombre': nombre,
      'correo': correo,
      'password': password,
      ...extra,
    });
    final tokens = (datos['tokens'] ?? {}) as Map<String, dynamic>;
    await guardarTokens(
      (tokens['access_token'] ?? '').toString(),
      (tokens['refresh_token'] ?? '').toString(),
    );
    return datos;
  }

  Future<Map<String, dynamic>> yo() => _peticion('GET', '/me');

  Future<Map<String, dynamic>> home() => _peticion('GET', '/home');

  Future<Map<String, dynamic>> dia(String fecha) =>
      _peticion('GET', '/days/$fecha');

  Future<List<dynamic>> categorias({String? tipo}) async {
    final datos = await _peticion(
      'GET',
      '/categories${tipo == null ? '' : '?tipo=$tipo'}',
    );
    return (datos['items'] as List<dynamic>?) ?? [];
  }

  Future<List<dynamic>> cuentas() async {
    final datos = await _peticion('GET', '/accounts');
    return (datos['items'] as List<dynamic>?) ?? [];
  }

  Future<Map<String, dynamic>> movimientos({
    int limite = 50,
    int desplazamiento = 0,
  }) =>
      _peticion('GET', '/transactions?limit=$limite&offset=$desplazamiento');

  /// Envia una frase escrita a mano.
  Future<Map<String, dynamic>> enviarTexto(
    String texto, {
    String? messageId,
    String origen = 'app_voz',
  }) =>
      _peticion('POST', '/messages', cuerpo: {
        'texto': texto,
        'message_id': messageId,
        'origen': origen,
      });

  /// Envia un audio WAV de 16 kHz mono. El backend lo transcribe.
  Future<Map<String, dynamic>> enviarAudio(
    Uint8List wav, {
    required String messageId,
    double duracion = 0,
    String idioma = 'es-CO',
  }) async {
    final peticion = http.MultipartRequest('POST', _uri('/messages'));
    peticion.headers.addAll(_cabeceras(json: false));
    peticion.fields['message_id'] = messageId;
    peticion.fields['idioma'] = idioma;
    if (duracion > 0) {
      peticion.fields['audio_duracion_s'] = duracion.toStringAsFixed(1);
    }
    peticion.files.add(
      http.MultipartFile.fromBytes('audio', wav, filename: 'audio.wav'),
    );

    try {
      final respuesta = await http.Response.fromStream(
        await _http.send(peticion).timeout(const Duration(seconds: 120)),
      );
      final datos = jsonDecode(respuesta.body) as Map<String, dynamic>;
      if (datos['ok'] == true) {
        return (datos['data'] ?? {}) as Map<String, dynamic>;
      }
      final error = (datos['error'] ?? {}) as Map<String, dynamic>;
      throw ApiError(
        (error['codigo'] ?? 'ERROR').toString(),
        (error['mensaje'] ?? 'Ocurrio un error.').toString(),
        estado: respuesta.statusCode,
      );
    } on ApiError {
      rethrow;
    } catch (_) {
      throw ApiError(
        'SIN_CONEXION',
        'No se pudo enviar el audio. Revisa la conexion con el backend.',
      );
    }
  }

  Future<Map<String, dynamic>> confirmarMensaje(int mensajeId) =>
      _peticion('POST', '/messages/$mensajeId/confirm');

  Future<Map<String, dynamic>> descartarMensaje(int mensajeId) =>
      _peticion('POST', '/messages/$mensajeId/discard');

  Future<Map<String, dynamic>> cerrarDia([String? fecha]) => _peticion(
        'POST',
        '/days/${fecha ?? _fechaLocal()}/close',
      );

  /// Fecha local en formato YYYY-MM-DD.
  static String _fechaLocal() {
    final ahora = DateTime.now();
    final mes = ahora.month.toString().padLeft(2, '0');
    final dia = ahora.day.toString().padLeft(2, '0');
    return '${ahora.year}-$mes-$dia';
  }

  Future<Map<String, dynamic>> resumenDiagnostico() =>
      _peticion('GET', '/metrics/diagnostics');
}
