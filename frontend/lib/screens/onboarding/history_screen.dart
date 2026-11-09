
import 'package:flutter/material.dart';

import 'package:frontend/theme/app_colors.dart';
import 'package:frontend/services/api_service.dart';
import 'package:frontend/services/auth_session.dart';

import 'package:frontend/screens/home_screen.dart';
import 'package:frontend/screens/metrics_screen.dart';
import 'package:frontend/screens/accounts_overview_screen.dart';

import 'filter_bottom_sheet.dart';
import '../../widgets/transaction_detail_bottom_sheet.dart';
import 'streak_screen.dart';
import 'notifications_screen.dart';
import 'count_perfil.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();

  String _selectedTab = 'Todos';
  late DateTime _selectedMonth;

  List<Map<String, dynamic>> _transactions = [];

  bool _isLoading = true;
  String? _error;
  int _requestVersion = 0;

  static const List<String> _months = [
    'Enero',
    'Febrero',
    'Marzo',
    'Abril',
    'Mayo',
    'Junio',
    'Julio',
    'Agosto',
    'Septiembre',
    'Octubre',
    'Noviembre',
    'Diciembre',
  ];

  @override
  void initState() {
    super.initState();

    final now = DateTime.now();
    _selectedMonth = DateTime(now.year, now.month, 1);

    _loadTransactions();
  }

  @override
  void dispose() {
    _requestVersion++;
    _searchController.dispose();
    super.dispose();
  }

  // ==========================================
  // FECHAS
  // ==========================================

  String _dateString(DateTime date) {
    final year = date.year.toString().padLeft(4, '0');
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');

    return '$year-$month-$day';
  }

  String get _monthTitle {
    return '${_months[_selectedMonth.month - 1]} ${_selectedMonth.year}';
  }

  String _dateLabel(String date) {
    final parsed = DateTime.tryParse(date);

    if (parsed == null) return date;

    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final movementDay = DateTime(
      parsed.year,
      parsed.month,
      parsed.day,
    );

    final difference = today.difference(movementDay).inDays;

    if (difference == 0) return 'Hoy';
    if (difference == 1) return 'Ayer';

    return '${parsed.day} de ${_months[parsed.month - 1].toLowerCase()}';
  }

  String _movementDate(Map<String, dynamic> movement) {
    final localDate = movement['fecha_local']?.toString();

    if (localDate != null && localDate.length >= 10) {
      return localDate.substring(0, 10);
    }

    final timestamp = movement['fecha_hora']?.toString();
    final parsed = timestamp == null
        ? null
        : DateTime.tryParse(timestamp);

    if (parsed == null) return '';

    return _dateString(parsed.toLocal());
  }

  String _movementTime(Map<String, dynamic> movement) {
    final raw = movement['fecha_hora']?.toString();

    if (raw == null || raw.isEmpty) return '';

    final parsed = DateTime.tryParse(raw);

    if (parsed == null) return '';

    final local = parsed.toLocal();
    final hour = local.hour % 12 == 0 ? 12 : local.hour % 12;
    final minute = local.minute.toString().padLeft(2, '0');
    final period = local.hour >= 12 ? 'PM' : 'AM';

    return '$hour:$minute $period';
  }

  // ==========================================
  // CARGAR MOVIMIENTOS DEL BACKEND
  // ==========================================

  Future<void> _loadTransactions() async {
    final version = ++_requestVersion;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final token = AuthSession.accessToken;

      if (token == null || token.isEmpty) {
        throw Exception(
          'No hay una sesión activa. Inicia sesión nuevamente.',
        );
      }

      final firstDay = DateTime(
        _selectedMonth.year,
        _selectedMonth.month,
        1,
      );

      final lastDay = DateTime(
        _selectedMonth.year,
        _selectedMonth.month + 1,
        0,
      );

      final List<Map<String, dynamic>> allMovements = [];

      const pageSize = 500;
      int offset = 0;

      // Consultamos todas las páginas para que
      // los totales mensuales no queden incompletos.
      while (true) {
        final response = await _apiService.getTransactions(
          accessToken: token,
          desde: _dateString(firstDay),
          hasta: _dateString(lastDay),
          limit: pageSize,
          offset: offset,
        );

        final dynamic payload = response['data'];

        if (payload is! Map) {
          throw Exception(
            'El servidor no devolvió los datos del historial.',
          );
        }

        final dynamic items = payload['items'];

        if (items is! List) {
          throw Exception(
            'El servidor no devolvió una lista de movimientos.',
          );
        }

        final page = items
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList();

        allMovements.addAll(page);

        final total = _toInt(payload['total']);

        offset += page.length;

        if (page.isEmpty ||
            offset >= total ||
            page.length < pageSize) {
          break;
        }
      }

      if (!mounted || version != _requestVersion) return;

      setState(() {
        _transactions = allMovements;
        _isLoading = false;
      });
    } catch (error) {
      if (!mounted || version != _requestVersion) return;

      setState(() {
        _isLoading = false;
        _error = error.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  Future<void> _changeMonth(int difference) async {
    setState(() {
      _selectedMonth = DateTime(
        _selectedMonth.year,
        _selectedMonth.month + difference,
        1,
      );
    });

    await _loadTransactions();
  }

  // ==========================================
  // CONVERSIÓN Y FORMATO DE DINERO
  // ==========================================

  int _toInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();

    return num.tryParse(value?.toString() ?? '')?.toInt() ?? 0;
  }

  String _money(int amount) {
    final digits = amount.abs().toString();
    final buffer = StringBuffer();

    for (int i = 0; i < digits.length; i++) {
      if (i > 0 && (digits.length - i) % 3 == 0) {
        buffer.write('.');
      }

      buffer.write(digits[i]);
    }

    return '\$${buffer.toString()}';
  }

  String _signedMoney(int amount) {
    if (amount > 0) return '+${_money(amount)}';
    if (amount < 0) return '-${_money(amount)}';

    return _money(0);
  }

  String _movementType(Map<String, dynamic> movement) {
    return movement['tipo']?.toString().toLowerCase() ?? '';
  }

  bool _isConfirmed(Map<String, dynamic> movement) {
    return movement['estado']?.toString().toLowerCase() ==
        'confirmado';
  }

  // ==========================================
  // RESUMEN DEL MES
  // ==========================================

  int get _monthlyIncome {
    int total = 0;

    for (final movement in _transactions) {
      if (_isConfirmed(movement) &&
          _movementType(movement) == 'ingreso') {
        total += _toInt(movement['monto']);
      }
    }

    return total;
  }

  int get _monthlyExpenses {
    int total = 0;

    for (final movement in _transactions) {
      if (_isConfirmed(movement) &&
          _movementType(movement) == 'gasto') {
        total += _toInt(movement['monto']);
      }
    }

    return total;
  }

  int get _monthlyBalance {
    return _monthlyIncome - _monthlyExpenses;
  }

  // ==========================================
  // FILTRAR MOVIMIENTOS
  // ==========================================

  List<Map<String, dynamic>> get _filteredTransactions {
    final search = _searchController.text.trim().toLowerCase();

    return _transactions.where((movement) {
      final type = _movementType(movement);

      bool matchesTab = true;

      if (_selectedTab == 'Gastos') {
        matchesTab = type == 'gasto';
      } else if (_selectedTab == 'Ingresos') {
        matchesTab = type == 'ingreso';
      } else if (_selectedTab == 'Ahorros') {
        matchesTab = type == 'ahorro';
      }

      final concept =
          movement['concepto']?.toString().toLowerCase() ?? '';

      final category =
          movement['categoria']?.toString().toLowerCase() ?? '';

      final account =
          movement['cuenta']?.toString().toLowerCase() ?? '';

      final goal =
          movement['meta']?.toString().toLowerCase() ?? '';

      final matchesSearch = search.isEmpty ||
          concept.contains(search) ||
          category.contains(search) ||
          account.contains(search) ||
          goal.contains(search);

      return matchesTab && matchesSearch;
    }).toList();
  }

  Map<String, List<Map<String, dynamic>>> get _groupedTransactions {
    final groups = <String, List<Map<String, dynamic>>>{};

    for (final movement in _filteredTransactions) {
      final date = _movementDate(movement);

      groups.putIfAbsent(date, () => []);
      groups[date]!.add(movement);
    }

    return groups;
  }

  // ==========================================
  // ICONOS SEGÚN CATEGORÍA
  // ==========================================

  IconData _iconForMovement(Map<String, dynamic> movement) {
    final type = _movementType(movement);

    if (type == 'ingreso') {
      return Icons.account_balance_wallet;
    }

    if (type == 'ahorro') {
      return Icons.savings_outlined;
    }

    final category =
        movement['categoria']?.toString().toLowerCase() ?? '';

    if (category.contains('aliment') ||
        category.contains('comida') ||
        category.contains('restaurante')) {
      return Icons.restaurant;
    }

    if (category.contains('transport')) {
      return Icons.directions_bus;
    }

    if (category.contains('vivienda') ||
        category.contains('hogar') ||
        category.contains('arriendo')) {
      return Icons.home_outlined;
    }

    if (category.contains('salud')) {
      return Icons.favorite_outline;
    }

    if (category.contains('educaci')) {
      return Icons.school_outlined;
    }

    if (category.contains('familia') ||
        category.contains('regalo')) {
      return Icons.card_giftcard;
    }

    if (category.contains('suscrip') ||
        category.contains('entretenimiento')) {
      return Icons.tv;
    }

    if (category.contains('ocio') ||
        category.contains('gustos')) {
      return Icons.celebration;
    }

    if (category.contains('ropa') ||
        category.contains('compras')) {
      return Icons.shopping_bag_outlined;
    }

    return Icons.receipt_long_outlined;
  }

  String _movementTitle(Map<String, dynamic> movement) {
    final concept = movement['concepto']?.toString().trim() ?? '';

    if (concept.isNotEmpty) return concept;

    final category = movement['categoria']?.toString().trim() ?? '';

    if (category.isNotEmpty) return category;

    switch (_movementType(movement)) {
      case 'ingreso':
        return 'Ingreso';
      case 'ahorro':
        return 'Ahorro';
      default:
        return 'Gasto';
    }
  }

  String _movementSubtitle(Map<String, dynamic> movement) {
    final parts = <String>[];

    final category = movement['categoria']?.toString().trim();
    final account = movement['cuenta']?.toString().trim();
    final goal = movement['meta']?.toString().trim();
    final time = _movementTime(movement);

    if (category != null && category.isNotEmpty) {
      parts.add(category);
    } else if (goal != null && goal.isNotEmpty) {
      parts.add(goal);
    }

    if (account != null && account.isNotEmpty) {
      parts.add(account);
    }

    if (time.isNotEmpty) {
      parts.add(time);
    }

    return parts.join(' • ');
  }

  String _movementAmount(Map<String, dynamic> movement) {
    final amount = _toInt(movement['monto']);
    final type = _movementType(movement);

    if (type == 'ingreso') return '+${_money(amount)}';

    return '-${_money(amount)}';
  }

  // ==========================================
  // CONSTRUIR PANTALLA
  // ==========================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // ==================================
            // BARRA SUPERIOR
            // ==================================

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
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.local_fire_department,
                                color: Colors.orange,
                                size: 18,
                              ),
                              SizedBox(width: 6),
                              Text(
                                '1 días',
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

                  // NOTIFICACIONES
                  Container(
                    width: 42,
                    height: 42,
                    decoration: const BoxDecoration(
                      color: AppColors.darkGreen,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                            const NotificationsScreen(),
                          ),
                        );
                      },
                      icon: const Icon(
                        Icons.notifications_none,
                        color: AppColors.cardCream,
                        size: 22,
                      ),
                      padding: EdgeInsets.zero,
                    ),
                  ),

                  const SizedBox(width: 10),

                  // PERFIL
                  Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      color: AppColors.darkGreen,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.cardCream,
                        width: 1.5,
                      ),
                    ),
                    child: IconButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                            const ProfileScreen(),
                          ),
                        );
                      },
                      icon: const Icon(
                        Icons.person_outline,
                        color: AppColors.cardCream,
                        size: 22,
                      ),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                ],
              ),
            ),

            // ==================================
            // CONTENIDO PRINCIPAL
            // ==================================

            Expanded(
              child: RefreshIndicator(
                color: AppColors.wine,
                onRefresh: _loadTransactions,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // SELECTOR DE MES
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildMonthButton(
                            Icons.chevron_left,
                                () => _changeMonth(-1),
                          ),

                          const SizedBox(width: 14),

                          Flexible(
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(
                                  Icons.calendar_month,
                                  color: AppColors.wine,
                                  size: 20,
                                ),
                                const SizedBox(width: 6),
                                Flexible(
                                  child: Text(
                                    _monthTitle,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      color: AppColors.wine,
                                      fontSize: 16,
                                      fontWeight: FontWeight.w900,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(width: 14),

                          _buildMonthButton(
                            Icons.chevron_right,
                                () => _changeMonth(1),
                          ),
                        ],
                      ),

                      const SizedBox(height: 14),

                      // TARJETA DE RESUMEN
                      Container(
                        padding: const EdgeInsets.symmetric(
                          vertical: 14,
                          horizontal: 10,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.cardCream,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: AppColors.darkGreen,
                            width: 1.5,
                          ),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            Expanded(
                              child: _buildSummaryItem(
                                'Ingresos',
                                '+${_money(_monthlyIncome)}',
                                AppColors.darkGreen,
                                Icons.north_east,
                              ),
                            ),

                            Container(
                              height: 32,
                              width: 1,
                              color: AppColors.wine.withValues(
                                alpha: 0.15,
                              ),
                            ),

                            Expanded(
                              child: _buildSummaryItem(
                                'Gastos',
                                '-${_money(_monthlyExpenses)}',
                                AppColors.wine,
                                Icons.south_west,
                              ),
                            ),

                            Container(
                              height: 32,
                              width: 1,
                              color: AppColors.wine.withValues(
                                alpha: 0.15,
                              ),
                            ),

                            Expanded(
                              child: _buildSummaryItem(
                                'Saldo',
                                _signedMoney(_monthlyBalance),
                                _monthlyBalance >= 0
                                    ? AppColors.darkGreen
                                    : AppColors.wine,
                                null,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 14),

                      // ==================================
                      // BÚSQUEDA Y FILTROS
                      // ==================================

                      Row(
                        children: [
                          Expanded(
                            child: Container(
                              height: 46,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 14,
                              ),
                              decoration: BoxDecoration(
                                color: AppColors.cardCream,
                                borderRadius: BorderRadius.circular(23),
                                border: Border.all(
                                  color: AppColors.darkGreen,
                                  width: 1.5,
                                ),
                              ),
                              child: Row(
                                children: [
                                  const Icon(
                                    Icons.search,
                                    color: AppColors.darkGreen,
                                    size: 20,
                                  ),

                                  const SizedBox(width: 8),

                                  Expanded(
                                    child: TextField(
                                      controller: _searchController,
                                      onChanged: (_) {
                                        setState(() {});
                                      },
                                      style: const TextStyle(
                                        color: AppColors.darkGreen,
                                        fontSize: 13,
                                      ),
                                      decoration: const InputDecoration(
                                        hintText: 'Busca por concepto',
                                        hintStyle: TextStyle(
                                          color: AppColors.darkGreen,
                                          fontSize: 13,
                                        ),
                                        border: InputBorder.none,
                                        isDense: true,
                                        contentPadding: EdgeInsets.zero,
                                      ),
                                    ),
                                  ),

                                  if (_searchController.text.isNotEmpty)
                                    GestureDetector(
                                      onTap: () {
                                        _searchController.clear();
                                        setState(() {});
                                      },
                                      child: const Icon(
                                        Icons.close,
                                        size: 18,
                                        color: AppColors.wine,
                                      ),
                                    ),
                                ],
                              ),
                            ),
                          ),

                          const SizedBox(width: 10),

                          GestureDetector(
                            onTap: () {
                              showModalBottomSheet(
                                context: context,
                                isScrollControlled: true,
                                backgroundColor: Colors.transparent,
                                builder: (context) =>
                                const FilterBottomSheet(),
                              );
                            },
                            child: Container(
                              width: 46,
                              height: 46,
                              decoration: BoxDecoration(
                                color: AppColors.cardCream,
                                borderRadius: BorderRadius.circular(23),
                                border: Border.all(
                                  color: AppColors.darkGreen,
                                  width: 1.5,
                                ),
                              ),
                              child: const Icon(
                                Icons.tune,
                                color: AppColors.wine,
                                size: 20,
                              ),
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 12),

                      // ==================================
                      // PESTAÑAS
                      // ==================================

                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            'Todos',
                            'Gastos',
                            'Ingresos',
                            'Ahorros',
                          ].map((tab) {
                            final isSelected = _selectedTab == tab;

                            return Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: ChoiceChip(
                                label: Text(tab),
                                selected: isSelected,
                                onSelected: (_) {
                                  setState(() {
                                    _selectedTab = tab;
                                  });
                                },
                                selectedColor: AppColors.wine,
                                backgroundColor: AppColors.cardCream,
                                labelStyle: TextStyle(
                                  color: isSelected
                                      ? AppColors.cardCream
                                      : AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12.5,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(20),
                                  side: BorderSide(
                                    color: isSelected
                                        ? AppColors.wine
                                        : AppColors.darkGreen,
                                    width: 1.5,
                                  ),
                                ),
                                showCheckmark: false,
                              ),
                            );
                          }).toList(),
                        ),
                      ),

                      const SizedBox(height: 16),

                      // ==================================
                      // LISTADO REAL DE MOVIMIENTOS
                      // ==================================

                      if (_isLoading)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 45),
                          child: Center(
                            child: CircularProgressIndicator(
                              color: AppColors.wine,
                            ),
                          ),
                        )
                      else if (_error != null)
                        _buildError()
                      else if (_filteredTransactions.isEmpty)
                          _buildEmptyState()
                        else
                          ..._buildGroupedMovements(),

                      const SizedBox(height: 16),

                      Center(
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.touch_app_outlined,
                              color: AppColors.darkGreen,
                              size: 14,
                            ),
                            const SizedBox(width: 4),
                            Flexible(
                              child: Text(
                                'Mostrando ${_monthTitle.toLowerCase()}. Desliza para actualizar.',
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  color: AppColors.darkGreen,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // ==================================
            // BARRA INFERIOR
            // ==================================

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
                          _buildNavItem(
                            icon: Icons.home_outlined,
                            label: 'Inicio',
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) =>
                                  const HomeScreen(),
                                ),
                              );
                            },
                          ),

                          _buildNavItem(
                            icon: Icons.bar_chart_rounded,
                            label: 'Métricas',
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) =>
                                  const MetricsScreen(),
                                ),
                              );
                            },
                          ),

                          _buildNavItem(
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

                          _buildNavItem(
                            icon: Icons.find_in_page_outlined,
                            label: 'Historial',
                            isSelected: true,
                            onTap: () {},
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(width: 8),

                  Container(
                    width: 50,
                    height: 50,
                    decoration: BoxDecoration(
                      color: AppColors.lime,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.darkGreen,
                        width: 2,
                      ),
                    ),
                    child: IconButton(
                      onPressed: () {},
                      icon: const Icon(
                        Icons.support_agent,
                        color: AppColors.darkGreen,
                        size: 24,
                      ),
                      padding: EdgeInsets.zero,
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

  // ==========================================
  // BOTONES PARA CAMBIAR MES
  // ==========================================

  Widget _buildMonthButton(
      IconData icon,
      VoidCallback onTap,
      ) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          color: AppColors.cardCream,
          shape: BoxShape.circle,
          border: Border.all(
            color: AppColors.darkGreen,
            width: 1.5,
          ),
        ),
        child: Icon(
          icon,
          color: AppColors.wine,
        ),
      ),
    );
  }

  // ==========================================
  // RESUMEN
  // ==========================================

  Widget _buildSummaryItem(
      String label,
      String amount,
      Color color,
      IconData? icon,
      ) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(
            color: AppColors.darkGreen,
            fontSize: 11,
            fontWeight: FontWeight.bold,
          ),
        ),

        const SizedBox(height: 3),

        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(
                icon,
                color: color,
                size: 14,
              ),
              const SizedBox(width: 2),
            ],

            Flexible(
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  amount,
                  maxLines: 1,
                  style: TextStyle(
                    color: color,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ==========================================
  // AGRUPAR MOVIMIENTOS POR FECHA
  // ==========================================

  List<Widget> _buildGroupedMovements() {
    final widgets = <Widget>[];
    final groups = _groupedTransactions;

    for (final entry in groups.entries) {
      final date = entry.key;
      final movements = entry.value;

      int dailyBalance = 0;

      for (final movement in movements) {
        final amount = _toInt(movement['monto']);
        final type = _movementType(movement);

        if (type == 'ingreso') {
          dailyBalance += amount;
        } else {
          dailyBalance -= amount;
        }
      }

      widgets.add(
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              _dateLabel(date),
              style: const TextStyle(
                color: AppColors.wine,
                fontWeight: FontWeight.w900,
                fontSize: 14.5,
              ),
            ),

            Text(
              _signedMoney(dailyBalance),
              style: TextStyle(
                color: dailyBalance > 0
                    ? AppColors.darkGreen
                    : AppColors.wine,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
          ],
        ),
      );

      widgets.add(const SizedBox(height: 8));

      for (final movement in movements) {
        widgets.add(
          _buildMovementCard(movement),
        );

        widgets.add(const SizedBox(height: 8));
      }

      widgets.add(const SizedBox(height: 8));
    }

    return widgets;
  }

  // ==========================================
  // TARJETA DE MOVIMIENTO REAL
  // ==========================================

  Widget _buildMovementCard(Map<String, dynamic> movement) {
    final title = _movementTitle(movement);
    final subtitle = _movementSubtitle(movement);
    final amount = _movementAmount(movement);
    final icon = _iconForMovement(movement);

    final type = _movementType(movement);
    final isIncome = type == 'ingreso';

    final state =
        movement['estado']?.toString().toLowerCase() ?? '';

    final isPending = state == 'pendiente';

    return _buildTransactionCard(
      title,
      subtitle,
      amount,
      icon,
      isIncome,
      isPending: isPending,
    );
  }

  // ==========================================
  // TARJETA ORIGINAL DEL DISEÑO
  // ==========================================

  Widget _buildTransactionCard(
      String title,
      String subtitle,
      String amount,
      IconData icon,
      bool isIncome, {
        bool isPending = false,
        bool isEdited = false,
      }) {
    return GestureDetector(
      onTap: () {
        showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (context) => TransactionDetailBottomSheet(
            title: title,
            subtitle: subtitle,
            amount: amount,
            icon: icon,
            isIncome: isIncome,
          ),
        );
      },
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 10,
        ),
        decoration: BoxDecoration(
          color: AppColors.cardCream,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppColors.darkGreen,
            width: 1.5,
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.mutedPink,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(
                icon,
                color: AppColors.wine,
                size: 20,
              ),
            ),

            const SizedBox(width: 12),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          title,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 13.5,
                          ),
                        ),
                      ),

                      if (isPending) ...[
                        const SizedBox(width: 6),

                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF7C474)
                                .withValues(alpha: 0.6),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.access_time,
                                size: 10,
                                color: AppColors.wine,
                              ),
                              SizedBox(width: 2),
                              Text(
                                'Pendiente',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontSize: 9,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],

                      if (isEdited) ...[
                        const SizedBox(width: 6),

                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.mutedPink,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            'Editado',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),

                  const SizedBox(height: 2),

                  Text(
                    subtitle,
                    style: const TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 10.5,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: 4),

            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isIncome
                      ? Icons.south_west
                      : Icons.north_east,
                  color: isIncome
                      ? AppColors.darkGreen
                      : AppColors.wine,
                  size: 14,
                ),

                const SizedBox(width: 2),

                Text(
                  amount,
                  style: TextStyle(
                    color: isIncome
                        ? AppColors.darkGreen
                        : AppColors.wine,
                    fontWeight: FontWeight.w900,
                    fontSize: 13.5,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================
  // ESTADO VACÍO
  // ==========================================

  Widget _buildEmptyState() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(
        horizontal: 20,
        vertical: 36,
      ),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.darkGreen,
          width: 1.5,
        ),
      ),
      child: const Column(
        children: [
          Icon(
            Icons.receipt_long_outlined,
            color: AppColors.wine,
            size: 42,
          ),

          SizedBox(height: 12),

          Text(
            'No hay movimientos',
            style: TextStyle(
              color: AppColors.wine,
              fontWeight: FontWeight.w900,
              fontSize: 16,
            ),
          ),

          SizedBox(height: 6),

          Text(
            'No encontramos movimientos para este mes y los filtros seleccionados.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.darkGreen,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // ERROR DE CONEXIÓN
  // ==========================================

  Widget _buildError() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.wine,
          width: 1.5,
        ),
      ),
      child: Column(
        children: [
          const Icon(
            Icons.error_outline,
            color: AppColors.wine,
            size: 38,
          ),

          const SizedBox(height: 10),

          const Text(
            'No pudimos cargar tu historial',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.wine,
              fontWeight: FontWeight.bold,
              fontSize: 15,
            ),
          ),

          const SizedBox(height: 8),

          Text(
            _error ?? 'Error desconocido',
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.darkGreen,
              fontSize: 12,
            ),
          ),

          const SizedBox(height: 14),

          ElevatedButton(
            onPressed: _loadTransactions,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.darkGreen,
              foregroundColor: AppColors.cardCream,
            ),
            child: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // NAVEGACIÓN INFERIOR
  // ==========================================

  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: 4,
          vertical: 2,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected
                  ? AppColors.lime
                  : AppColors.darkGreen,
              size: 24,
            ),

            const SizedBox(height: 2),

            Text(
              label,
              style: TextStyle(
                color: isSelected
                    ? AppColors.lime
                    : AppColors.darkGreen,
                fontSize: 10,
                fontWeight: isSelected
                    ? FontWeight.bold
                    : FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
