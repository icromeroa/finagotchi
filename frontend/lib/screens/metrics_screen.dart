import 'package:flutter/material.dart';
import 'package:frontend/services/api_service.dart';
import 'package:frontend/services/auth_session.dart';
import 'package:frontend/theme/app_colors.dart';


import 'onboarding/streak_screen.dart';
import 'onboarding/notifications_screen.dart';
import 'onboarding/count_perfil.dart';
import 'home_screen.dart';
import 'accounts_overview_screen.dart';
import 'onboarding/history_screen.dart';


class MetricsScreen extends StatefulWidget {
  const MetricsScreen({super.key});

  @override
  State<MetricsScreen> createState() => _MetricsScreenState();
}

class _MetricsScreenState extends State<MetricsScreen> {
  int selectedTab = 2;
  final ApiService _api = ApiService();
  DateTime _fecha = DateTime.now();
  Map<String, dynamic> _metricas = {};
  List<Map<String, dynamic>> _transacciones = [];
  bool _cargando = true;
  String? _error;
  int _requestId = 0;

  @override
  void initState() {
    super.initState();
    _cargarMetricas();
  }

  String _fechaApi(DateTime fecha) =>
      '${fecha.year.toString().padLeft(4, '0')}-${fecha.month.toString().padLeft(2, '0')}-${fecha.day.toString().padLeft(2, '0')}';

  Map<String, dynamic> _map(dynamic valor) =>
      valor is Map ? Map<String, dynamic>.from(valor) : {};

  List<Map<String, dynamic>> _lista(dynamic valor) => valor is List
      ? valor.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
      : [];

  double _numero(dynamic valor) => valor is num
      ? valor.toDouble()
      : double.tryParse(valor?.toString() ?? '') ?? 0;

  String _dinero(num valor, {bool signo = false}) {
    final n = valor.round();
    final texto = n.abs().toString().replaceAllMapped(
      RegExp(r'\B(?=(\d{3})+(?!\d))'), (m) => '.',
    );
    return '${n < 0 ? '-' : signo && n > 0 ? '+' : ''}\$$texto';
  }

  Map<String, dynamic> get _resumen => _map(_metricas['resumen']);

  double get _ingresos => _numero(
    selectedTab == 0
        ? _resumen['total_ingresos']
        : _resumen['ingresos'],
  );

  double get _gastos => _numero(
    selectedTab == 0
        ? _resumen['total_gastos']
        : _resumen['gastos'],
  );

  double get _balance => _numero(_resumen['balance_neto'] ?? (_ingresos - _gastos));

  DateTime get _inicioPeriodo {
    if (selectedTab == 0) return _fecha;
    if (selectedTab == 1) return _fecha.subtract(const Duration(days: 6));
    return DateTime(_fecha.year, _fecha.month, 1);
  }

  Future<void> _cargarMetricas() async {
    final token = AuthSession.accessToken;
    final id = ++_requestId;
    setState(() { _cargando = true; _error = null; });
    if (token == null || token.isEmpty) {
      setState(() { _cargando = false; _error = 'Inicia sesión para consultar tus métricas.'; });
      return;
    }
    try {
      final fecha = _fechaApi(_fecha);
      final Future<Map<String, dynamic>> peticion = selectedTab == 0
          ? _api.getDailyMetrics(accessToken: token, fecha: fecha)
          : selectedTab == 1
          ? _api.getWeeklyMetrics(accessToken: token, fecha: fecha)
          : _api.getMonthlyMetrics(accessToken: token, fecha: fecha);
      final respuesta = await peticion;
      final movimientos = await _api.getTransactions(
        accessToken: token,
        desde: _fechaApi(_inicioPeriodo),
        hasta: fecha,
        estado: 'confirmado',
        limit: 100,
      );
      if (!mounted || id != _requestId) return;
      // La API envuelve el contenido en data cuando responde ok=true.
      final datos = _map(respuesta['data'] ?? respuesta['datos'] ?? respuesta);
      final historial = movimientos['data'] ?? movimientos['datos'] ?? movimientos;
      final lista = historial is List ? historial :
      _map(historial)['transacciones'] ?? _map(historial)['items'] ?? _map(historial)['movimientos'] ?? [];
      setState(() {
        _metricas = datos;
        _transacciones = _lista(lista);
        _cargando = false;
      });
    } catch (e) {
      if (!mounted || id != _requestId) return;
      setState(() { _cargando = false; _error = e.toString(); });
    }
  }

  void _cambiarTab(int tab) {
    if (selectedTab == tab) return;
    setState(() => selectedTab = tab);
    _cargarMetricas();
  }

  void _moverPeriodo(int sentido) {
    setState(() {
      if (selectedTab == 0) {
        _fecha = _fecha.add(Duration(days: sentido));
      } else if (selectedTab == 1) {
        _fecha = _fecha.add(Duration(days: 7 * sentido));
      } else {
        final mes = DateTime(_fecha.year, _fecha.month + sentido + 1, 0);
        _fecha = DateTime(mes.year, mes.month, _fecha.day.clamp(1, mes.day));
      }
      if (_fecha.isAfter(DateTime.now())) _fecha = DateTime.now();
    });
    _cargarMetricas();
  }

  String _nombreMes(int mes) => const [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ][mes - 1];

  String _nombreCategoria(Map<String, dynamic> item) =>
      (item['categoria'] ?? item['nombre'] ?? 'Sin categoría').toString();

  IconData _iconoCategoria(String nombre) {
    final n = nombre.toLowerCase();
    if (n.contains('aliment') || n.contains('comida')) return Icons.restaurant;
    if (n.contains('transporte')) return Icons.directions_bus;
    if (n.contains('vivienda') || n.contains('hogar')) return Icons.home_outlined;
    if (n.contains('ocio') || n.contains('entreten')) return Icons.local_activity_outlined;
    if (n.contains('café') || n.contains('micro')) return Icons.coffee_outlined;
    return Icons.category_outlined;
  }

  List<Map<String, dynamic>> get _categorias {
    if (selectedTab != 1) return _lista(_metricas['categorias']);
    final agrupadas = <String, double>{};
    for (final t in _transacciones) {
      if (t['tipo'] != 'gasto') continue;
      final nombre = (t['categoria_nombre'] ?? t['categoria'] ?? 'Sin categoría').toString();
      agrupadas[nombre] = (agrupadas[nombre] ?? 0) + _numero(t['monto']);
    }
    return agrupadas.entries.map((e) => {'categoria': e.key, 'total': e.value}).toList()
      ..sort((a, b) => _numero(b['total']).compareTo(_numero(a['total'])));
  }

  List<Map<String, dynamic>> get _categoriasVisuales => _categorias.map((c) {
    final total = _numero(c['total']);
    final nombre = _nombreCategoria(c);
    return <String, dynamic>{
      'icon': _iconoCategoria(nombre),
      'name': nombre,
      'amount': _dinero(total),
      'progress': _gastos > 0 ? (total / _gastos).clamp(0.0, 1.0) : 0.0,
    };
  }).toList();

  double _gastoDia(DateTime fecha) {
    if (selectedTab == 1) {
      for (final dia in _lista(_metricas['dias'])) {
        if (dia['fecha_local'] == _fechaApi(fecha)) return _numero(dia['gastos']);
      }
      return 0;
    }
    return _transacciones.where((t) => t['tipo'] == 'gasto' &&
        (t['fecha_local'] ?? t['fecha'])?.toString().startsWith(_fechaApi(fecha)) == true)
        .fold<double>(0, (s, t) => s + _numero(t['monto']));
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // 1. BARRA SUPERIOR
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const StreakScreen(),
                        ),
                      );
                    },
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 14,
                            vertical: 7,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.cardCream,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: AppColors.wine,
                              width: 1.5,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.local_fire_department,
                                color: Colors.orange,
                                size: 18,
                              ),
                              SizedBox(width: 6),
                              Text(
                                'Racha',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 3),
                        const Padding(
                          padding: EdgeInsets.only(left: 4),
                          child: Text(
                            '• Registra hoy para mantenerla',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 9.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const NotificationsScreen(),
                        ),
                      );
                    },
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: AppColors.darkGreen,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppColors.darkGreen,
                          width: 1.5,
                        ),
                      ),
                      child: const Icon(
                        Icons.notifications_none,
                        color: AppColors.cardCream,
                        size: 20,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const ProfileScreen(),
                        ),
                      );
                    },
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: AppColors.darkGreen,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppColors.darkGreen,
                          width: 1.5,
                        ),
                      ),
                      child: const Icon(
                        Icons.person_outline,
                        color: AppColors.cardCream,
                        size: 20,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // 2. PESTAÑAS
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 8,
              ),
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: AppColors.wine.withOpacity(0.3),
                  ),
                ),
                child: Row(
                  children: [
                    _buildTabButton('Diario', 0),
                    _buildTabButton('Semanal', 1),
                    _buildTabButton('Mensual', 2),
                  ],
                ),
              ),
            ),

            // 3. CONTENIDO DINÁMICO
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                child: Column(
                  children: [
                    _buildDateSelectorHeader(),
                    const SizedBox(height: 14),
                    if (_cargando) const Padding(
                      padding: EdgeInsets.all(32),
                      child: CircularProgressIndicator(color: AppColors.wine),
                    ) else if (_error != null) Column(children: [
                      Text(_error!, textAlign: TextAlign.center),
                      TextButton(onPressed: _cargarMetricas, child: const Text('Reintentar')),
                    ]) else RefreshIndicator(
                      onRefresh: _cargarMetricas,
                      child: Column(children: [
                        if (selectedTab == 0) _buildDailyView(),
                        if (selectedTab == 1) _buildWeeklyView(),
                        if (selectedTab == 2) _buildMonthlyView(),
                      ]),
                    ),
                  ],
                ),
              ),
            ),

            // 4. BARRA INFERIOR DE NAVEGACIÓN
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(30),
                        border: Border.all(
                          color: AppColors.darkGreen,
                          width: 2,
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildCustomNavItem(
                            icon: Icons.home_outlined,
                            label: 'Inicio',
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => const HomeScreen(),
                                ),
                              );
                            },
                          ),
                          _buildCustomNavItem(
                            icon: Icons.bar_chart_rounded,
                            label: 'Métricas',
                            isSelected: true,
                            onTap: () {},
                          ),
                          _buildCustomNavItem(
                            icon: Icons.account_balance_wallet_outlined,
                            label: 'Cuentas',
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) =>
                                  const AccountsOverviewScreen(),
                                ),
                              );
                            },
                          ),
                          _buildCustomNavItem(
                            icon: Icons.find_in_page_outlined,
                            label: 'Historial',
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) =>
                                  const HistoryScreen(),
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: () {},
                    child: Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        color: AppColors.lime,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppColors.darkGreen,
                          width: 2,
                        ),
                      ),
                      child: const Icon(
                        Icons.mic,
                        color: AppColors.darkGreen,
                        size: 22,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTabButton(String title, int index) {
    final isSelected = selectedTab == index;

    return Expanded(
      child: GestureDetector(
        onTap: () => _cambiarTab(index),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.wine : Colors.transparent,
            borderRadius: BorderRadius.circular(20),
          ),
          alignment: Alignment.center,
          child: Text(
            title,
            style: TextStyle(
              color: isSelected ? AppColors.cream : AppColors.wine,
              fontWeight: FontWeight.bold,
              fontSize: 13,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDateSelectorHeader() {
    String label;
    if (selectedTab == 0) {
      label = '${_fecha.day} de ${_nombreMes(_fecha.month)} de ${_fecha.year}';
    } else if (selectedTab == 1) {
      final inicio = _inicioPeriodo;
      label = '${inicio.day}/${inicio.month} - ${_fecha.day}/${_fecha.month}/${_fecha.year}';
    } else {
      label = '${_nombreMes(_fecha.month)} ${_fecha.year}';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.wine.withOpacity(0.2)),
      ),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        IconButton(onPressed: () => _moverPeriodo(-1),
            icon: const Icon(Icons.chevron_left, color: AppColors.wine)),
        Flexible(child: Text(label, textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12.5))),
        IconButton(onPressed: _fechaApi(_fecha) == _fechaApi(DateTime.now()) ? null : () => _moverPeriodo(1),
            icon: const Icon(Icons.chevron_right, color: AppColors.wine)),
      ]),
    );
  }

  Widget _flujoReal(String titulo) => _buildFlowCard(
    income: _dinero(_ingresos, signo: true),
    expense: _dinero(-_gastos),
    net: _dinero(_balance, signo: true),
    title: titulo,
  );

  Widget _buildDailyView() {
    return Column(
      children: [
        _flujoReal('Flujo del Día'),
        const SizedBox(height: 14),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: AppColors.wine.withOpacity(0.15),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Distribución del Día',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                  ),
                  Icon(
                    Icons.pie_chart_outline,
                    color: AppColors.wine,
                    size: 18,
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Center(
                child: SizedBox(
                  width: 110,
                  height: 110,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      const CircularProgressIndicator(
                        value: 1.0,
                        backgroundColor: AppColors.cream,
                        color: AppColors.wine,
                        strokeWidth: 12,
                      ),
                      const Icon(
                        Icons.pie_chart,
                        color: AppColors.wine,
                        size: 36,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),
              if (_categorias.isEmpty)
                const Text('Sin gastos registrados para este día.'),
              ..._categorias.map((c) {
                final nombre = _nombreCategoria(c);
                final monto = _numero(c['total']);
                return Padding(padding: const EdgeInsets.only(bottom: 8),
                    child: _buildCategoryDetailRow(_iconoCategoria(nombre), nombre,
                        '${_gastos > 0 ? (monto * 100 / _gastos).toStringAsFixed(1) : '0'}% (${_dinero(monto)})', AppColors.wine));
              }),
              const SizedBox(height: 16),
              const Text('DESGLOSE DE HOY', style: TextStyle(color: AppColors.darkGreen,
                  fontSize: 10, fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              if (_transacciones.isEmpty)
                const Text('No hay movimientos confirmados.'),
              ..._transacciones.take(10).map((t) {
                final nombre = (t['concepto'] ?? t['descripcion'] ?? 'Movimiento').toString();
                final categoria = (t['categoria_nombre'] ?? t['categoria'] ?? 'Sin categoría').toString();
                return Padding(padding: const EdgeInsets.only(bottom: 8),
                    child: _buildTransactionItem(nombre,
                        (t['fecha_local'] ?? t['fecha'] ?? '').toString(),
                        _dinero(_numero(t['monto']) * (t['tipo'] == 'gasto' ? -1 : 1), signo: true),
                        categoria, _iconoCategoria(categoria)));
              }),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _buildCompactTipCard(),
      ],
    );
  }

  Widget _buildWeeklyView() {
    return Column(
      children: [
        _flujoReal('Flujo Semanal'),
        const SizedBox(height: 14),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: AppColors.wine.withOpacity(0.15),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Rutina de Gastos',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink.withOpacity(0.4),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: AppColors.wine.withOpacity(0.2),
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.warning_amber_rounded,
                          color: AppColors.wine,
                          size: 12,
                        ),
                        SizedBox(width: 4),
                        Text(
                          'Gastos por día',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: List.generate(7, (i) {
                  final fecha = _inicioPeriodo.add(Duration(days: i));
                  final monto = _gastoDia(fecha);
                  final maximo = List.generate(7, (j) =>
                      _gastoDia(_inicioPeriodo.add(Duration(days: j))))
                      .fold<double>(0, (a, b) => a > b ? a : b);
                  const nombres = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];
                  return _buildWeeklyBarColumn(nombres[fecha.weekday - 1],
                      maximo == 0 ? 0 : monto / maximo, _dinero(monto),
                      isWine: monto > 0 && monto == maximo,
                      isPink: monto > 0 && monto != maximo,
                      showTopLabel: monto > 0);
                }),
              ),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.cream,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: AppColors.wine.withOpacity(0.15),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.lightbulb_outline,
                      color: AppColors.wine,
                      size: 18,
                    ),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _gastos == 0 ? 'Aún no hay gastos esta semana.' : 'Tu gasto semanal es ${_dinero(_gastos)}.',
                        style: TextStyle(
                          color: AppColors.wine,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          height: 1.2,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _buildCategoriesBreakdownList(
          total: _dinero(_gastos),
          items: _categoriasVisuales,
        ),
        const SizedBox(height: 14),
        _buildCompactTipCard(),
      ],
    );
  }

  Widget _buildMonthlyView() {
    return Column(
      children: [
        _flujoReal('Flujo Consolidado'),
        const SizedBox(height: 14),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: AppColors.wine.withOpacity(0.15),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Curva de Gasto Acumulado',
                        style: TextStyle(
                          color: AppColors.wine,
                          fontWeight: FontWeight.bold,
                          fontSize: 13.5,
                        ),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'Aceleración y mesetas semanales',
                        style: TextStyle(
                          color: AppColors.darkGreen,
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.lime,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${_fecha.day} días',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Icon(Icons.remove, color: AppColors.wine, size: 16),
                  Text(
                    ' Real  ',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Icon(Icons.remove, color: AppColors.darkGreen, size: 16),
                  Text(
                    ' Acumulado',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Container(
                height: 130,
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  color: AppColors.cream,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: AppColors.wine.withOpacity(0.15),
                  ),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Expanded(
                      child: LayoutBuilder(builder: (context, constraints) {
                        double acumulado = 0;
                        final acumulados = List<double>.generate(_fecha.day, (i) {
                          acumulado += _gastoDia(DateTime(_fecha.year, _fecha.month, i + 1));
                          return acumulado;
                        });
                        final maximo = acumulados.isEmpty ? 0.0 : acumulados.last;
                        return Row(crossAxisAlignment: CrossAxisAlignment.end,
                            children: acumulados.map((v) => Expanded(child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 1),
                              child: Container(
                                height: maximo > 0 ? constraints.maxHeight * v / maximo : 2,
                                decoration: BoxDecoration(color: AppColors.wine,
                                    borderRadius: BorderRadius.circular(2)),
                              ),
                            ))).toList());
                      }),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Día 1',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 9.5,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'Día 7',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 9.5,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'Día 15',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 9.5,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'Día 22',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 9.5,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'Día 30',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 9.5,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.cream,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: AppColors.wine.withOpacity(0.15),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.lightbulb_outline,
                      color: AppColors.wine,
                      size: 18,
                    ),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _gastos == 0 ? 'Aún no hay gastos registrados este mes.' : 'Has acumulado ${_dinero(_gastos)} en gastos este mes.',
                        style: TextStyle(
                          color: AppColors.wine,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          height: 1.2,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _buildCategoriesBreakdownList(
          total: _dinero(_gastos),
          items: _categoriasVisuales,
        ),
        const SizedBox(height: 14),
        _buildCompactTipCard(),
      ],
    );
  }

  Widget _buildFlowCard({
    required String income,
    required String expense,
    required String net,
    required String title,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.15),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 13.5,
                ),
              ),
              const Icon(
                Icons.account_balance_wallet_outlined,
                color: AppColors.wine,
                size: 18,
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    vertical: 12,
                    horizontal: 8,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.cardCream,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: AppColors.wine.withOpacity(0.3),
                      width: 1.5,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.wine.withOpacity(0.15),
                        offset: const Offset(0, 3),
                        blurRadius: 0,
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: AppColors.lime,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 6),
                          const Text(
                            'Ingresos',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        income,
                        style: const TextStyle(
                          color: AppColors.darkGreen,
                          fontSize: 15,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    vertical: 12,
                    horizontal: 8,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink.withOpacity(0.35),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: AppColors.wine.withOpacity(0.2),
                      width: 1,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.wine.withOpacity(0.15),
                        offset: const Offset(0, 3),
                        blurRadius: 0,
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 6,
                            height: 6,
                            decoration: const BoxDecoration(
                              color: AppColors.wine,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Text(
                            'Egresos',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        expense,
                        style: const TextStyle(
                          color: AppColors.wine,
                          fontSize: 15,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(
              vertical: 10,
              horizontal: 14,
            ),
            decoration: BoxDecoration(
              color: AppColors.lime,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.check_circle_outline,
                          color: AppColors.darkGreen,
                          size: 12,
                        ),
                        SizedBox(width: 4),
                        Text(
                          'BALANCE NETO',
                          style: TextStyle(
                            color: AppColors.darkGreen,
                            fontSize: 9,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Capacidad libre de ahorro',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 9.5,
                      ),
                    ),
                  ],
                ),
                Text(
                  net,
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 14.5,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeeklyBarColumn(
      String day,
      double heightFactor,
      String amountLabel, {
        bool isCream = false,
        bool isPink = false,
        bool isWine = false,
        bool isLime = false,
        bool showTopLabel = false,
        bool hasFlame = false,
      }) {
    Color barColor = AppColors.cardCream;

    if (isPink) barColor = AppColors.mutedPink;
    if (isWine) barColor = AppColors.wine;
    if (isLime) barColor = AppColors.lime;

    return Column(
      children: [
        if (showTopLabel)
          Text(
            amountLabel,
            style: const TextStyle(
              color: AppColors.wine,
              fontSize: 9,
              fontWeight: FontWeight.bold,
            ),
          ),
        if (!showTopLabel) const SizedBox(height: 13),
        const SizedBox(height: 4),
        Container(
          width: 26,
          height: 90 * heightFactor,
          decoration: BoxDecoration(
            color: barColor,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: AppColors.wine.withOpacity(0.2),
            ),
          ),
          alignment: Alignment.topCenter,
          child: hasFlame
              ? const Padding(
            padding: EdgeInsets.only(top: 4),
            child: Icon(
              Icons.local_fire_department,
              color: Colors.orange,
              size: 14,
            ),
          )
              : null,
        ),
        const SizedBox(height: 6),
        Text(
          day,
          style: const TextStyle(
            color: AppColors.wine,
            fontWeight: FontWeight.bold,
            fontSize: 11,
          ),
        ),
      ],
    );
  }

  Widget _buildCategoryDetailRow(
      IconData icon,
      String title,
      String subtitle,
      Color color,
      ) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.cream,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: AppColors.wine.withOpacity(0.2),
            ),
          ),
          child: Icon(icon, color: color, size: 16),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
              Text(
                subtitle,
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 10,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildTransactionItem(
      String title,
      String subtitle,
      String amount,
      String tag,
      IconData icon,
      ) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.15),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.wine, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 11.5,
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 9.5,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                amount,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.w900,
                  fontSize: 11.5,
                ),
              ),
              Text(
                tag,
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 9,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCategoriesBreakdownList({
    required String total,
    required List items,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.15),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Desglose por Categorías',
                style: TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 13.5,
                ),
              ),
              Text(
                total,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.w900,
                  fontSize: 13.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...items.map(
                (item) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                children: [
                  Icon(
                    item['icon'],
                    color: AppColors.wine,
                    size: 18,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              item['name'],
                              style: const TextStyle(
                                color: AppColors.wine,
                                fontWeight: FontWeight.bold,
                                fontSize: 11.5,
                              ),
                            ),
                            Text(
                              item['amount'],
                              style: const TextStyle(
                                color: AppColors.wine,
                                fontWeight: FontWeight.bold,
                                fontSize: 11.5,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: item['progress'],
                            backgroundColor: AppColors.cream,
                            color: AppColors.wine,
                            minHeight: 6,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCompactTipCard() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.mutedPink.withOpacity(0.4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.15),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.lightbulb_outline,
            color: AppColors.wine,
            size: 18,
          ),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Nancy tip: Registrar pequeños gastos diarios reduce la fatiga mental a fin de mes.',
              style: TextStyle(
                color: AppColors.wine,
                fontSize: 11,
                fontWeight: FontWeight.w500,
                height: 1.2,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCustomNavItem({
    required IconData icon,
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: isSelected ? AppColors.darkGreen : AppColors.wine,
            size: 22,
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(
              color: isSelected ? AppColors.darkGreen : AppColors.wine,
              fontSize: 10,
              fontWeight:
              isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}
