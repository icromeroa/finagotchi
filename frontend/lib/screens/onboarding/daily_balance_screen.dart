
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../services/api_service.dart';
import '../../services/auth_session.dart';

class DailyBalanceScreen extends StatefulWidget {
  const DailyBalanceScreen({super.key});

  @override
  State<DailyBalanceScreen> createState() => _DailyBalanceScreenState();
}

class _DailyBalanceScreenState extends State<DailyBalanceScreen> {
  final ApiService _apiService = ApiService();

  bool _loading = true;
  String? _error;
  DateTime _fecha = DateTime.now();

  Map<String, dynamic> _resumen = {};
  List<Map<String, dynamic>> _movimientos = [];

  @override
  void initState() {
    super.initState();
    _cargarDatos();
  }

  String _fechaApi(DateTime fecha) {
    return '${fecha.year}-'
        '${fecha.month.toString().padLeft(2, '0')}-'
        '${fecha.day.toString().padLeft(2, '0')}';
  }

  String get _fechaVisible {
    const dias = [
      'LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES',
      'VIERNES', 'SÁBADO', 'DOMINGO'
    ];

    const meses = [
      'ENERO', 'FEBRERO', 'MARZO', 'ABRIL',
      'MAYO', 'JUNIO', 'JULIO', 'AGOSTO',
      'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'
    ];

    return '${dias[_fecha.weekday - 1]}, '
        '${_fecha.day} DE ${meses[_fecha.month - 1]}';
  }

  Map<String, dynamic> _mapa(dynamic value) {
    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }
    return {};
  }

  List<Map<String, dynamic>> _lista(dynamic value) {
    if (value is List) {
      return value
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    }
    return [];
  }

  double _numero(dynamic value) {
    if (value is num) return value.toDouble();

    if (value is String) {
      final limpio = value
          .replaceAll('\$', '')
          .replaceAll('COP', '')
          .replaceAll(' ', '')
          .replaceAll('.', '')
          .replaceAll(',', '.');

      return double.tryParse(limpio) ?? 0;
    }

    return 0;
  }

  String _dinero(double valor) {
    final entero = valor.abs().round().toString();
    final partes = <String>[];

    for (int i = entero.length; i > 0; i -= 3) {
      final inicio = i - 3 < 0 ? 0 : i - 3;
      partes.insert(0, entero.substring(inicio, i));
    }

    return '\$${partes.join('.')}';
  }

  dynamic _primerValor(
      Map<String, dynamic> datos,
      List<String> claves,
      ) {
    for (final clave in claves) {
      if (datos[clave] != null) {
        return datos[clave];
      }
    }
    return null;
  }

  Future<void> _cargarDatos() async {
    final token = AuthSession.accessToken;

    if (token == null || token.isEmpty) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = 'Debes iniciar sesión para consultar tu balance.';
      });
      return;
    }

    final hoy = DateTime.now();
    final fecha = _fechaApi(hoy);

    setState(() {
      _loading = true;
      _error = null;
      _fecha = hoy;
    });

    try {
      final respuesta = await _apiService.getDailyMetrics(
        accessToken: token,
        fecha: fecha,
      );

      final data = _mapa(respuesta['data']);
      final resumen = _mapa(data['resumen']);

      // La consulta de movimientos complementa el resumen.
      // Si falla, todavía podemos mostrar las métricas.
      List<Map<String, dynamic>> movimientos = [];

      try {
        final transacciones = await _apiService.getTransactions(
          accessToken: token,
          desde: fecha,
          hasta: fecha,
          estado: 'confirmado',
          limit: 100,
        );

        final contenido = transacciones['data'];

        if (contenido is List) {
          movimientos = _lista(contenido);
        } else {
          final datos = _mapa(contenido);
          movimientos = _lista(
            _primerValor(datos, [
              'transacciones',
              'movimientos',
              'items',
              'results',
            ]),
          );
        }
      } catch (_) {
        // Conservamos las métricas si falla el historial.
      }

      if (!mounted) return;

      setState(() {
        _resumen = resumen.isNotEmpty ? resumen : data;
        _movimientos = movimientos;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  double get _ingresos => _numero(
    _primerValor(_resumen, [
      'total_ingresos',
      'ingresos',
    ]),
  );

  double get _gastos => _numero(
    _primerValor(_resumen, [
      'total_gastos',
      'gastos',
    ]),
  );

  double get _balance {
    final valor = _primerValor(_resumen, [
      'balance_neto',
      'saldo_neto',
    ]);

    if (valor != null) return _numero(valor);
    return _ingresos - _gastos;
  }

  // Este porcentaje representa la proporción de gastos
  // respecto a los ingresos del día, NO una calificación
  // de salud financiera.
  double? get _porcentajeGasto {
    if (_ingresos <= 0) return null;
    return (_gastos / _ingresos * 100).clamp(0.0, 999.0);
  }

  String get _mensajeNancy {
    if (_ingresos == 0 && _gastos == 0) {
      return '¡Hola! Soy Nancy 🐷. Todavía no tienes ingresos '
          'ni gastos registrados hoy. Cuando registres '
          'tus movimientos, podremos revisar tu balance.';
    }

    if (_balance > 0) {
      return '¡Buen trabajo! Hoy tus ingresos superan '
          'tus gastos. Terminaste con un balance positivo '
          'de ${_dinero(_balance)} COP. ¡Sigue así! 🐷';
    }

    if (_balance < 0) {
      return 'Hoy tus gastos superaron tus ingresos '
          'por ${_dinero(_balance)} COP. Podemos revisar '
          'en qué categorías gastaste más para organizar '
          'mejor tu dinero. 🐷';
    }

    return 'Hoy tus ingresos y gastos están equilibrados. '
        'Revisemos tus movimientos para seguir cuidando '
        'tus finanzas. 🐷';
  }


  String _nombreCategoria(Map<String, dynamic> movimiento) {
    final categoria = movimiento['categoria'];

    // El historial utiliza la categoría como texto.
    if (categoria is String && categoria.trim().isNotEmpty) {
      return categoria.trim();
    }

    // También admite una categoría como objeto.
    if (categoria is Map) {
      final nombre = categoria['nombre'];
      if (nombre != null && nombre.toString().trim().isNotEmpty) {
        return nombre.toString().trim();
      }
    }

    final nombre = movimiento['categoria_nombre'] ??
        movimiento['nombre_categoria'];

    if (nombre != null && nombre.toString().trim().isNotEmpty) {
      return nombre.toString().trim();
    }

    return 'Sin categoría';
  }


  List<Map<String, dynamic>> get _categorias {
    final agrupadas = <String, double>{};

    for (final movimiento in _movimientos) {
      final tipo = (movimiento['tipo'] ?? '').toString().toLowerCase();

      if (tipo != 'gasto') continue;

      final nombre = _nombreCategoria(movimiento);
      final monto = _numero(movimiento['monto']).abs();

      agrupadas[nombre] = (agrupadas[nombre] ?? 0) + monto;
    }

    final resultado = agrupadas.entries.map((entrada) {
      return <String, dynamic>{
        'nombre': entrada.key,
        'monto': entrada.value,
      };
    }).toList();

    resultado.sort(
          (a, b) => (b['monto'] as double)
          .compareTo(a['monto'] as double),
    );

    return resultado;
  }

  IconData _iconoCategoria(String nombre) {
    final texto = nombre.toLowerCase();

    if (texto.contains('aliment') ||
        texto.contains('comida') ||
        texto.contains('restaurante')) {
      return Icons.restaurant;
    }

    if (texto.contains('transport')) {
      return Icons.directions_bus;
    }

    if (texto.contains('café') ||
        texto.contains('cafe') ||
        texto.contains('snack')) {
      return Icons.coffee_outlined;
    }

    if (texto.contains('salud')) {
      return Icons.favorite_outline;
    }

    if (texto.contains('educa')) {
      return Icons.school_outlined;
    }

    if (texto.contains('entreten')) {
      return Icons.movie_outlined;
    }

    if (texto.contains('suscrip')) {
      return Icons.subscriptions_outlined;
    }

    return Icons.local_offer_outlined;
  }

  Widget _tarjetaResumen({
    required String titulo,
    required String valor,
    required String subtitulo,
    required IconData icono,
    required Color color,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.cream,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    titulo,
                    style: TextStyle(
                      color: color,
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Icon(icono, color: color, size: 14),
              ],
            ),
            const SizedBox(height: 6),
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Text(
                valor,
                style: TextStyle(
                  color: color,
                  fontSize: 16,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitulo,
              style: TextStyle(
                color: color,
                fontSize: 9,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _filaCategoria(Map<String, dynamic> categoria) {
    final nombre = categoria['nombre'].toString();
    final monto = _numero(categoria['monto']);
    final porcentaje = _gastos > 0
        ? (monto / _gastos * 100).clamp(0.0, 100.0)
        : 0.0;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.cream,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _iconoCategoria(nombre),
                  color: AppColors.darkGreen,
                  size: 18,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  nombre,
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${_dinero(monto)} COP',
                    style: const TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.w900,
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    '${porcentaje.toStringAsFixed(1)}% del gasto',
                    style: const TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 7),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: porcentaje / 100,
              backgroundColor: AppColors.cream,
              color: AppColors.mutedPink,
              minHeight: 5,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final porcentaje = _porcentajeGasto;
    final categorias = _categorias;

    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // BARRA SUPERIOR
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: const BoxDecoration(
                      color: AppColors.mutedPink,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.check,
                      color: AppColors.wine,
                      size: 16,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Balance del Día',
                      style: TextStyle(
                        color: AppColors.wine,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  IconButton(
                    onPressed: _loading ? null : _cargarDatos,
                    icon: const Icon(
                      Icons.refresh,
                      color: AppColors.wine,
                    ),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Container(
                      width: 34,
                      height: 34,
                      decoration: const BoxDecoration(
                        color: AppColors.mutedPink,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.close,
                        color: AppColors.wine,
                        size: 18,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: _loading
                  ? const Center(
                child: CircularProgressIndicator(
                  color: AppColors.wine,
                ),
              )
                  : _error != null
                  ? Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.cloud_off_outlined,
                        color: AppColors.wine,
                        size: 40,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _error!,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: AppColors.wine,
                        ),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _cargarDatos,
                        child: const Text('Reintentar'),
                      ),
                    ],
                  ),
                ),
              )
                  : RefreshIndicator(
                onRefresh: _cargarDatos,
                color: AppColors.wine,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(
                    16, 0, 16, 24,
                  ),
                  children: [
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 5,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.mutedPink,
                          borderRadius:
                          BorderRadius.circular(16),
                        ),
                        child: const Text(
                          'ETAPA 1 - DIAGNÓSTICO DIARIO',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 9.5,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Center(
                      child: Text(
                        _fechaVisible,
                        style: const TextStyle(
                          color: AppColors.wine,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // TARJETA PRINCIPAL
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius:
                        BorderRadius.circular(24),
                        border: Border.all(
                          color: AppColors.wine
                              .withValues(alpha: 0.15),
                        ),
                      ),
                      child: Column(
                        children: [
                          Stack(
                            alignment: Alignment.center,
                            children: [
                              SizedBox(
                                width: 110,
                                height: 110,
                                child: CircularProgressIndicator(
                                  value: porcentaje == null
                                      ? 0
                                      : (porcentaje / 100)
                                      .clamp(0.0, 1.0),
                                  backgroundColor:
                                  AppColors.cream,
                                  color: AppColors.lime,
                                  strokeWidth: 10,
                                ),
                              ),
                              Column(
                                children: [
                                  Text(
                                    porcentaje == null
                                        ? '—'
                                        : '${porcentaje.toStringAsFixed(0)}%',
                                    style: const TextStyle(
                                      color: AppColors.wine,
                                      fontSize: 26,
                                      fontWeight:
                                      FontWeight.w900,
                                    ),
                                  ),
                                  const Text(
                                    'GASTOS / INGRESOS',
                                    style: TextStyle(
                                      color:
                                      AppColors.darkGreen,
                                      fontSize: 8.5,
                                      fontWeight:
                                      FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Proporción de gastos frente a ingresos de hoy',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 10,
                            ),
                          ),
                          const SizedBox(height: 16),

                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: AppColors.cream,
                              borderRadius:
                              BorderRadius.circular(16),
                              border: Border.all(
                                color: AppColors.wine
                                    .withValues(alpha: 0.1),
                              ),
                            ),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                    children: [
                                      const Text(
                                        'SALDO NETO DEL DÍA',
                                        style: TextStyle(
                                          color:
                                          AppColors.darkGreen,
                                          fontSize: 9.5,
                                          fontWeight:
                                          FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      FittedBox(
                                        fit: BoxFit.scaleDown,
                                        alignment:
                                        Alignment.centerLeft,
                                        child: Text(
                                          '${_balance >= 0 ? '+' : '-'}${_dinero(_balance)} COP',
                                          style: const TextStyle(
                                            color: AppColors.wine,
                                            fontSize: 20,
                                            fontWeight:
                                            FontWeight.w900,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Container(
                                  padding:
                                  const EdgeInsets.symmetric(
                                    horizontal: 10,
                                    vertical: 6,
                                  ),
                                  decoration: BoxDecoration(
                                    color: AppColors.lime,
                                    borderRadius:
                                    BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    _balance > 0
                                        ? 'Superávit'
                                        : _balance < 0
                                        ? 'Déficit'
                                        : 'Equilibrio',
                                    style: const TextStyle(
                                      color: AppColors.darkGreen,
                                      fontSize: 11,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              _tarjetaResumen(
                                titulo: 'Ingresos Totales',
                                valor: '+${_dinero(_ingresos)}',
                                subtitulo: 'Ingresos del día',
                                icono: Icons.arrow_upward,
                                color: AppColors.darkGreen,
                              ),
                              const SizedBox(width: 10),
                              _tarjetaResumen(
                                titulo: 'Gastos Totales',
                                valor: '-${_dinero(_gastos)}',
                                subtitulo: 'Gastos del día',
                                icono: Icons.arrow_downward,
                                color: AppColors.wine,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // NANCY COACH
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink
                            .withValues(alpha: 0.4),
                        borderRadius:
                        BorderRadius.circular(20),
                        border: Border.all(
                          color: AppColors.wine
                              .withValues(alpha: 0.15),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment:
                        CrossAxisAlignment.start,
                        children: [
                          const Row(
                            children: [
                              CircleAvatar(
                                radius: 14,
                                backgroundColor: AppColors.wine,
                                child: Icon(
                                  Icons.smart_toy,
                                  color: AppColors.cardCream,
                                  size: 16,
                                ),
                              ),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Análisis de Nancy Coach',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.w900,
                                    fontSize: 13,
                                  ),
                                ),
                              ),
                              Icon(
                                Icons.verified_outlined,
                                color: AppColors.wine,
                                size: 18,
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Resumen automático del día',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _mensajeNancy,
                            style: const TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 11,
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // GASTOS POR CATEGORÍA
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius:
                        BorderRadius.circular(20),
                        border: Border.all(
                          color: AppColors.wine
                              .withValues(alpha: 0.15),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment:
                        CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Expanded(
                                child: Text(
                                  'Gastos por Categoría',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight:
                                    FontWeight.w900,
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                              Container(
                                padding:
                                const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.lime,
                                  borderRadius:
                                  BorderRadius.circular(12),
                                ),
                                child: Text(
                                  '${categorias.length} categorías',
                                  style: const TextStyle(
                                    color:
                                    AppColors.darkGreen,
                                    fontSize: 10,
                                    fontWeight:
                                    FontWeight.bold,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          if (categorias.isEmpty)
                            const Padding(
                              padding:
                              EdgeInsets.symmetric(vertical: 16),
                              child: Center(
                                child: Text(
                                  'No hay categorías de gastos disponibles para hoy.',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            )
                          else
                            ...categorias.map(_filaCategoria),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
