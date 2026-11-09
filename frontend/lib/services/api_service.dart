
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl;

  ApiService({
    this.baseUrl = const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:5000/api/v1',
    ),
  });

  // ==============================
  // REGISTRO
  // ==============================

  Future<Map<String, dynamic>> register({
    required String nombre,
    required String correo,
    required String password,
    bool aceptaTerminos = false,
  }) async {
    return _post(
      '/auth/register',
      {
        'nombre': nombre,
        'correo': correo,
        'password': password,
        'acepta_terminos': aceptaTerminos,
      },
    );
  }

  // ==============================
  // INICIO DE SESIÓN
  // ==============================

  Future<Map<String, dynamic>> login({
    required String correo,
    required String password,
  }) async {
    return _post(
      '/auth/login',
      {
        'correo': correo,
        'password': password,
      },
    );
  }

  // ==============================
  // RENOVAR TOKENS
  // ==============================

  Future<Map<String, dynamic>> refresh({
    required String refreshToken,
  }) async {
    return _post(
      '/auth/refresh',
      {
        'refresh_token': refreshToken,
      },
    );
  }

  // ==============================
  // CERRAR SESIÓN
  // ==============================

  Future<Map<String, dynamic>> logout({
    required String accessToken,
    String? refreshToken,
  }) async {
    return _post(
      '/auth/logout',
      {
        if (refreshToken != null)
          'refresh_token': refreshToken,
      },
      accessToken: accessToken,
    );
  }

  // ==============================
  // OBTENER USUARIO
  // ==============================

  Future<Map<String, dynamic>> getMe({
    required String accessToken,
  }) async {
    return _get(
      '/me',
      accessToken: accessToken,
    );
  }

  // ==============================
  // OBTENER INFORMACIÓN DEL HOME
  // ==============================

  Future<Map<String, dynamic>> getHome({
    required String accessToken,
  }) async {
    return _get(
      '/home',
      accessToken: accessToken,
    );
  }

  // ==============================
  // OBTENER CUENTAS
  // ==============================

  Future<List<Map<String, dynamic>>> getAccounts({
    required String accessToken,
  }) async {
    final data = await _get('/accounts', accessToken: accessToken);
    final items = data['items'] ?? data['data'] ?? data;
    if (items is List) {
      return items.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
    return [];
  }

  // ==============================
  // OBTENER CATEGORÍAS
  // ==============================

  Future<Map<String, dynamic>> getCategories({
    required String accessToken,
  }) async {
    return _get(
      '/categories',
      accessToken: accessToken,
    );
  }

  // ==============================
  // OBTENER METAS
  // ==============================

  Future<List<Map<String, dynamic>>> getGoals({
    required String accessToken,
  }) async {
    final data = await _get(
      '/goals',
      accessToken: accessToken,
    );
    final items = data['items'] ?? data['data'] ?? data;
    if (items is List) {
      return items.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
    return [];
  }

  // ==============================
  // OBTENER MÉTRICAS DIARIAS
  // ==============================

  Future<Map<String, dynamic>> getDailyMetrics({
    required String accessToken,
    required String fecha,
  }) async {
    final uri = Uri.parse(
      '$baseUrl/metrics/daily',
    ).replace(
      queryParameters: {
        'fecha': fecha,
      },
    );

    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer $accessToken',
        'Accept': 'application/json',
      },
    );

    return _handleResponse(response);
  }

  // ==============================
  // REGISTRAR MOVIMIENTO
  // ==============================

  Future<Map<String, dynamic>> createTransaction({
    required String accessToken,
    required String tipo,
    required int monto,
    int? categoriaId,
    int? cuentaId,
    int? metaId,
    String? concepto,
  }) async {
    return _post(
      '/transactions',
      {
        'tipo': tipo,
        'monto': monto,
        if (categoriaId != null)
          'categoria_id': categoriaId,
        if (cuentaId != null)
          'cuenta_id': cuentaId,
        if (metaId != null)
          'meta_id': metaId,
        if (concepto != null && concepto.isNotEmpty)
          'concepto': concepto,
        'origen': 'manual',
        'estado': 'confirmado',
      },
      accessToken: accessToken,
    );
  }

  // ==============================
  // OBTENER HISTORIAL DE MOVIMIENTOS
  // ==============================

  Future<Map<String, dynamic>> getTransactions({
    required String accessToken,
    String? tipo,
    String? desde,
    String? hasta,
    int? categoriaId,
    int? cuentaId,
    String? estado,
    int? montoMin,
    int? montoMax,
    int limit = 100,
    int offset = 0,
  }) async {
    final query = <String, String>{
      'limit': limit.toString(),
      'offset': offset.toString(),
      if (tipo != null && tipo.isNotEmpty)
        'tipo': tipo,
      if (desde != null && desde.isNotEmpty)
        'desde': desde,
      if (hasta != null && hasta.isNotEmpty)
        'hasta': hasta,
      if (categoriaId != null)
        'categoria_id': categoriaId.toString(),
      if (cuentaId != null)
        'cuenta_id': cuentaId.toString(),
      if (estado != null && estado.isNotEmpty)
        'estado': estado,
      if (montoMin != null)
        'monto_min': montoMin.toString(),
      if (montoMax != null)
        'monto_max': montoMax.toString(),
    };

    final uri = Uri.parse(
      '$baseUrl/transactions',
    ).replace(
      queryParameters: query,
    );

    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer $accessToken',
        'Accept': 'application/json',
      },
    );

    return _handleResponse(response);
  }

  // ==============================
  // DISPOSITIVOS (vinculación)
  // ==============================

  Future<Map<String, dynamic>> registerDevice({
    required String deviceUid,
    String? modelo,
    String? firmware,
  }) async {
    return _post(
      '/device/register',
      {
        'device_uid': deviceUid,
        if (modelo != null) 'modelo': modelo,
        if (firmware != null) 'firmware': firmware,
      },
    );
  }

  Future<Map<String, dynamic>> pairDevice({
    required String deviceUid,
    required String pin,
    required String accessToken,
  }) async {
    return _post(
      '/device/pair',
      {
        'device_uid': deviceUid,
        'pin': pin,
      },
      accessToken: accessToken,
    );
  }

  Future<Map<String, dynamic>> claimDevice({
    required String deviceUid,
    required String pin,
  }) async {
    return _post(
      '/device/claim',
      {
        'device_uid': deviceUid,
        'pin': pin,
      },
    );
  }

  Future<Map<String, dynamic>> unlinkDevice({
    required String deviceUid,
    required String accessToken,
  }) async {
    return _post(
      '/device/unlink',
      {
        'device_uid': deviceUid,
      },
      accessToken: accessToken,
    );
  }

  Future<Map<String, dynamic>> listDevices({
    required String accessToken,
  }) async {
    return _get(
      '/device',
      accessToken: accessToken,
    );
  }

  // ==============================
  // MÉTODO INTERNO GET
  // ==============================

  Future<Map<String, dynamic>> _get(
      String endpoint, {
        required String accessToken,
      }) async {
    final response = await http.get(
      Uri.parse('$baseUrl$endpoint'),
      headers: {
        'Authorization': 'Bearer $accessToken',
        'Accept': 'application/json',
      },
    );

    return _handleResponse(response);
  }

  // ==============================
  // MÉTODO INTERNO POST
  // ==============================

  Future<Map<String, dynamic>> _post(
      String endpoint,
      Map<String, dynamic> data, {
        String? accessToken,
      }) async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    if (accessToken != null) {
      headers['Authorization'] = 'Bearer $accessToken';
    }

    final response = await http.post(
      Uri.parse('$baseUrl$endpoint'),
      headers: headers,
      body: jsonEncode(data),
    );

    return _handleResponse(response);
  }

  // ==============================
  // INTERPRETAR RESPUESTAS
  // ==============================

  Map<String, dynamic> _handleResponse(
      http.Response response,
      ) {
    Map<String, dynamic> result;

    try {
      final decoded = jsonDecode(response.body);

      result = Map<String, dynamic>.from(decoded);
    } catch (_) {
      throw Exception(
        'El servidor devolvió una respuesta que no es JSON.',
      );
    }

    if (response.statusCode >= 200 &&
        response.statusCode < 300 &&
        result['ok'] == true) {
      return result;
    }

    final errorData = result['error'];

    if (errorData is Map) {
      throw Exception(
        errorData['mensaje'] ??
            'Error al comunicarse con el servidor.',
      );
    }

    throw Exception(
      'Error del servidor: ${response.statusCode}',
    );
  }
}
