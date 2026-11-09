
import 'package:flutter/material.dart';
import 'package:frontend/theme/app_colors.dart';
import 'package:frontend/services/auth_session.dart';
import 'package:frontend/services/api_service.dart';

import 'package:frontend/screens/onboarding/streak_screen.dart';
import 'package:frontend/screens/onboarding/notifications_screen.dart';
import 'package:frontend/screens/onboarding/daily_balance_screen.dart';

import 'package:frontend/screens/metrics_screen.dart';
import 'package:frontend/screens/accounts_overview_screen.dart';
import 'package:frontend/screens/onboarding/history_screen.dart';
import 'package:frontend/screens/onboarding/count_perfil.dart';

import 'package:frontend/widgets/voice_recording_modal.dart';
import 'package:frontend/widgets/manual_register_modal.dart';
import 'package:frontend/widgets/top_icon_buttons.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService apiService = ApiService();

  bool isLoading = true;
  String? errorMessage;

  Map<String, dynamic> homeData = {};
  Map<String, dynamic> dailyData = {};
  List<Map<String, dynamic>> categories = [];
  List<Map<String, dynamic>> goals = [];

  @override
  void initState() {
    super.initState();
    _loadHomeData();
  }

  // ============================================================
  // CARGAR INFORMACIÓN DEL BACKEND
  // ============================================================

  Future<void> _loadHomeData() async {
    final token = AuthSession.accessToken;

    if (token == null || token.isEmpty) {
      if (!mounted) return;

      setState(() {
        isLoading = false;
        errorMessage = 'No hay una sesión activa. Inicia sesión nuevamente.';
      });
      return;
    }

    if (!mounted) return;

    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final homeResponse = await apiService.getHome(
        accessToken: token,
      );

      final home = Map<String, dynamic>.from(
        homeResponse['data'] ?? {},
      );

      final fecha = home['fecha_local']?.toString();

      if (fecha == null || fecha.isEmpty) {
        throw Exception('El backend no devolvió la fecha del usuario.');
      }

      final responses = await Future.wait([
        apiService.getDailyMetrics(
          accessToken: token,
          fecha: fecha,
        ),
        apiService.getGoals(
          accessToken: token,
        ),
      ]);

      final dailyResponse = responses[0];
      final goalsResponse = responses[1];

      final daily = Map<String, dynamic>.from(
        dailyResponse['data'] ?? {},
      );

      final rawGoals = goalsResponse['data'];

      final goalsList = rawGoals is List
          ? rawGoals
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList()
          : <Map<String, dynamic>>[];

      final rawCategories = daily['categorias'];

      final categoriesList = rawCategories is List
          ? rawCategories
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList()
          : <Map<String, dynamic>>[];

      if (!mounted) return;

      setState(() {
        homeData = home;
        dailyData = daily;
        categories = categoriesList;
        goals = goalsList;
        isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isLoading = false;
        errorMessage = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  // ============================================================
  // FUNCIONES PARA LEER LOS DATOS DE FORMA SEGURA
  // ============================================================

  int _number(dynamic value) {
    if (value is num) return value.toInt();
    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  double _decimal(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0;
  }

  dynamic _firstValue(
      Map<String, dynamic> data,
      List<String> keys,
      ) {
    for (final key in keys) {
      if (data.containsKey(key) && data[key] != null) {
        return data[key];
      }
    }
    return null;
  }

  String _money(dynamic value) {
    final amount = _number(value);
    final formatted = amount.abs().toString().replaceAllMapped(
      RegExp(r'\B(?=(\d{3})+(?!\d))'),
          (match) => '.',
    );

    return '${amount < 0 ? '-' : ''}\$$formatted';
  }

  double _percentage(int part, int total) {
    if (total <= 0) return 0;
    return (part / total).clamp(0.0, 1.0);
  }

  int _percentageText(double value) {
    return (value * 100).round();
  }

  // ============================================================
  // DATOS DEL HOME
  // ============================================================

  Map<String, dynamic> get _today {
    final value = homeData['hoy'];
    return value is Map
        ? Map<String, dynamic>.from(value)
        : {};
  }

  Map<String, dynamic> get _mascot {
    final value = homeData['mascota'];
    return value is Map
        ? Map<String, dynamic>.from(value)
        : {};
  }

  Map<String, dynamic> get _progress {
    final value = homeData['progreso'];
    return value is Map
        ? Map<String, dynamic>.from(value)
        : {};
  }

  int get _budget => _number(_today['presupuesto_diario']);

  int get _spent => _number(_today['gastos']);

  int get _remaining => _number(_today['cupo_restante']);

  int get _points => _number(homeData['puntos']);

  int get _totalCategoryExpenses {
    return categories.fold(
      0,
          (sum, item) => sum + _number(item['total']),
    );
  }

  // ============================================================
  // PROGRESO DE ETAPA
  // ============================================================

  double get _stageProgress {
    final value = _firstValue(
      _progress,
      [
        'porcentaje',
        'porcentaje_progreso',
        'progreso_porcentaje',
        'avance',
      ],
    );

    if (value == null) return 0;

    final number = _decimal(value);

    if (number > 1) {
      return (number / 100).clamp(0.0, 1.0);
    }

    return number.clamp(0.0, 1.0);
  }

  String get _stageText {
    final stage = _firstValue(
      _progress,
      ['etapa_actual', 'numero_etapa', 'etapa'],
    );

    final day = _firstValue(
      _progress,
      ['dia_actual', 'dia', 'dias_completados'],
    );

    if (stage != null && day != null) {
      return 'Etapa $stage de 3 • Día $day de 28';
    }

    return 'Tu progreso financiero';
  }

  // ============================================================
  // META ACTIVA
  // ============================================================

  Map<String, dynamic>? get _activeGoal {
    for (final goal in goals) {
      final state = goal['estado']?.toString().toLowerCase();

      if (state == null ||
          state == 'activa' ||
          state == 'en_progreso' ||
          state == 'en progreso') {
        return goal;
      }
    }

    return goals.isNotEmpty ? goals.first : null;
  }

  int _goalSaved(Map<String, dynamic> goal) {
    return _number(
      _firstValue(
        goal,
        [
          'monto_actual',
          'monto_ahorrado',
          'total_ahorrado',
          'ahorro_actual',
          'ahorrado',
        ],
      ),
    );
  }

  int _goalTarget(Map<String, dynamic> goal) {
    return _number(
      _firstValue(
        goal,
        [
          'monto_meta',
          'monto_objetivo',
          'objetivo',
        ],
      ),
    );
  }

  // ============================================================
  // MODAL DE GRABACIÓN DE VOZ
  // ============================================================

  void _openVoiceRecordingModal() {
    final token = AuthSession.accessToken ?? '';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => VoiceRecordingModal(
        accessToken: token,

        onSuccess: (data) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('¡Movimiento guardado correctamente! 🐷'),
            ),
          );

          _loadHomeData();
        },

        onManualRegister: () {
          Navigator.pop(context);
          _openManualRegisterModal();
        },
      ),
    );
  }

  // ============================================================
  // MODAL DE REGISTRO MANUAL
  // ============================================================

  void _openManualRegisterModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => ManualRegisterModal(
        onBackToVoice: () {
          Navigator.pop(context);
          _openVoiceRecordingModal();
        },

        // NUEVO: actualizar Home después de guardar
        onSaved: () {
          _loadHomeData();
        },
      ),
    );
  }

  // ============================================================
  // NAVEGACIÓN A HISTORIAL
  // ============================================================

  void _openHistoryScreen() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const HistoryScreen(),
      ),
    );
  }

  // ============================================================
  // ICONOS DE CATEGORÍAS
  // ============================================================

  IconData _categoryIcon(String name) {
    final category = name.toLowerCase();

    if (category.contains('aliment')) {
      return Icons.restaurant;
    }

    if (category.contains('transporte')) {
      return Icons.directions_bus;
    }

    if (category.contains('café') ||
        category.contains('cafe') ||
        category.contains('mecato')) {
      return Icons.coffee_outlined;
    }

    if (category.contains('salud')) {
      return Icons.medical_services_outlined;
    }

    if (category.contains('hogar')) {
      return Icons.home_outlined;
    }

    if (category.contains('entreten')) {
      return Icons.movie_outlined;
    }

    return Icons.shopping_bag_outlined;
  }

  // ============================================================
  // PANTALLA DE CARGA Y ERROR
  // ============================================================

  Widget _buildLoadingScreen() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            color: AppColors.darkGreen,
          ),
          SizedBox(height: 16),
          Text(
            'Nancy está preparando tu habitación...',
            style: TextStyle(
              color: AppColors.darkGreen,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorScreen() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.cloud_off_outlined,
              size: 55,
              color: AppColors.wine,
            ),
            const SizedBox(height: 16),
            const Text(
              'No pudimos cargar tu Home',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.wine,
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              errorMessage ?? 'Ocurrió un error inesperado.',
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.darkGreen,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _loadHomeData,
              icon: const Icon(Icons.refresh),
              label: const Text('Intentar nuevamente'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.darkGreen,
                foregroundColor: AppColors.cream,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // BUILD PRINCIPAL
  // ============================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // BARRA SUPERIOR
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
                            children: const [
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

                  NotificationButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) =>
                          const NotificationsScreen(),
                        ),
                      );
                    },
                  ),

                  const SizedBox(width: 10),

                  ProfileIconButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const ProfileScreen(),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),

            // CONTENIDO
            Expanded(
              child: isLoading
                  ? _buildLoadingScreen()
                  : errorMessage != null
                  ? _buildErrorScreen()
                  : RefreshIndicator(
                color: AppColors.darkGreen,
                onRefresh: _loadHomeData,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(
                    16,
                    4,
                    16,
                    16,
                  ),
                  child: Column(
                    children: [
                      _buildStageCard(),

                      // GLOBO DE DIÁLOGO
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(
                          vertical: 10,
                          horizontal: 16,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.cardCream,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: AppColors.wine,
                            width: 1.5,
                          ),
                        ),
                        child: Text(
                          '¡Hola, ${_mascot['nombre'] ?? 'Nancy'}! ¿Qué tal si me cuentas tu primer gasto?',
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ),

                      const SizedBox(height: 2),

                      const Icon(
                        Icons.arrow_drop_down,
                        color: AppColors.wine,
                        size: 28,
                      ),

                      const SizedBox(height: 2),

                      // HABITACIÓN Y NANCY
                      Container(
                        height: 315,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: AppColors.cardCream,
                          borderRadius: BorderRadius.circular(24),
                          border: Border.all(
                            color: AppColors.wine,
                            width: 1.5,
                          ),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(23),
                          child: Stack(
                            children: [
                              Positioned.fill(
                                child: Image.asset(
                                  'assets/images/Habitacion_rosa.png',
                                  fit: BoxFit.contain,
                                ),
                              ),
                              Positioned(
                                bottom: 25,
                                left: 0,
                                right: 0,
                                child: Center(
                                  child: Image.asset(
                                    'assets/images/nancy_ojos_corazon.png',
                                    width: 150,
                                    height: 100,
                                    fit: BoxFit.contain,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),

                      const SizedBox(height: 14),

                      // FINALIZA TU DÍA
                      Center(
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) =>
                                  const DailyBalanceScreen(),
                                ),
                              );
                            },
                            borderRadius: BorderRadius.circular(25),
                            child: Container(
                              height: 50,
                              width: 280,
                              decoration: BoxDecoration(
                                color: const Color(0xFFF7C474),
                                borderRadius:
                                BorderRadius.circular(25),
                                border: const Border(
                                  bottom: BorderSide(
                                    color: AppColors.wine,
                                    width: 3.5,
                                  ),
                                ),
                              ),
                              child: const Center(
                                child: Text(
                                  'Finaliza tu día',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.w900,
                                    fontSize: 15,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 12),

                      // HABLAR Y ESCRIBIR
                      _buildActionButtons(),

                      const SizedBox(height: 16),

                      // CUPO DIARIO
                      _buildDailyBudgetCard(),

                      const SizedBox(height: 14),

                      // CATEGORÍAS Y META
                      _buildCategoriesAndGoalCard(),
                    ],
                  ),
                ),
              ),
            ),

            // BARRA INFERIOR
            _buildBottomNavigation(),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // TARJETA DE PROGRESO
  // ============================================================

  Widget _buildStageCard() {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 14,
        vertical: 8,
      ),
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: AppColors.lime.withOpacity(0.4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.darkGreen.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              _stageText,
              style: const TextStyle(
                color: AppColors.darkGreen,
                fontSize: 10.5,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          SizedBox(
            width: 50,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: _stageProgress,
                backgroundColor: AppColors.cream,
                color: AppColors.darkGreen,
                minHeight: 6,
              ),
            ),
          ),
          const SizedBox(width: 6),
          Text(
            '$_points pts',
            style: const TextStyle(
              color: AppColors.darkGreen,
              fontSize: 10.5,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // BOTONES HABLAR Y ESCRIBIR
  // ============================================================

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          flex: 6,
          child: GestureDetector(
            onTap: _openVoiceRecordingModal,
            child: Container(
              height: 54,
              padding: const EdgeInsets.symmetric(horizontal: 10),
              decoration: BoxDecoration(
                color: const Color(0xFFCBE394),
                borderRadius: BorderRadius.circular(27),
                border: const Border(
                  bottom: BorderSide(
                    color: AppColors.darkGreen,
                    width: 3.5,
                  ),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: const BoxDecoration(
                      color: AppColors.darkGreen,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.mic,
                      color: Color(0xFFCBE394),
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Flexible(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          'Mantén para hablar',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: AppColors.darkGreen,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                        Text(
                          '“Almuerzo corriente 14 mil”',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: AppColors.darkGreen,
                            fontSize: 9.5,
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

        const SizedBox(width: 10),

        Expanded(
          flex: 4,
          child: GestureDetector(
            onTap: _openManualRegisterModal,
            child: Container(
              height: 54,
              decoration: BoxDecoration(
                color: const Color(0xFFF3C4D4),
                borderRadius: BorderRadius.circular(27),
                border: const Border(
                  bottom: BorderSide(
                    color: AppColors.wine,
                    width: 3.5,
                  ),
                ),
              ),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.notes,
                    color: AppColors.wine,
                    size: 20,
                  ),
                  SizedBox(width: 6),
                  Text(
                    'Escribir',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ============================================================
  // TARJETA CUPO DIARIO LIBRE
  // ============================================================

  Widget _buildDailyBudgetCard() {
    final availableProgress = _budget > 0
        ? (_remaining / _budget).clamp(0.0, 1.0)
        : 0.0;

    final availablePercentage = _percentageText(availableProgress);

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
              const Row(
                children: [
                  Icon(
                    Icons.account_balance_wallet_outlined,
                    color: AppColors.wine,
                    size: 18,
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Cupo Diario Libre',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
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
                  _remaining >= 0 ? 'seguro' : 'excedido',
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 6),

          const Text(
            'Disponible hoy',
            style: TextStyle(
              color: AppColors.darkGreen,
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 2),

          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                _money(_remaining),
                style: const TextStyle(
                  color: AppColors.wine,
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const Spacer(),
              Text(
                'Presupuesto diario\n${_money(_budget)}',
                textAlign: TextAlign.right,
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 10,
                  height: 1.2,
                ),
              ),
            ],
          ),

          const SizedBox(height: 10),

          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: availableProgress,
              backgroundColor: AppColors.cream,
              color: AppColors.darkGreen,
              minHeight: 8,
            ),
          ),

          const SizedBox(height: 8),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${_money(_spent)} gastados',
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '$availablePercentage% disponible',
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ============================================================
  // CATEGORÍAS Y META ACTIVA
  // ============================================================

  Widget _buildCategoriesAndGoalCard() {
    final goal = _activeGoal;

    final saved = goal == null ? 0 : _goalSaved(goal);
    final target = goal == null ? 0 : _goalTarget(goal);

    final goalProgress = target > 0
        ? (saved / target).clamp(0.0, 1.0)
        : 0.0;

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
              const Row(
                children: [
                  Icon(
                    Icons.pie_chart_outline,
                    color: AppColors.darkGreen,
                    size: 18,
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Gastos por categoría',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
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
                  '${categories.length} categorías',
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          if (categories.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 14),
              child: Center(
                child: Text(
                  'Todavía no tienes gastos registrados hoy.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 11,
                  ),
                ),
              ),
            )
          else
            ...categories.map((category) {
              final name = category['categoria']?.toString() ??
                  'Sin categoría';

              final amount = _number(category['total']);
              final percentage = _percentage(
                amount,
                _totalCategoryExpenses,
              );

              final records = _number(category['num_registros']);

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _buildCategoryRow(
                  icon: _categoryIcon(name),
                  title: name,
                  subtitle:
                  '$records ${records == 1 ? 'registro' : 'registros'}',
                  amount: '${_money(amount)} COP',
                  percentage:
                  '${_percentageText(percentage)}% del gasto',
                  progress: percentage,
                ),
              );
            }),

          const SizedBox(height: 4),

          // META ACTIVA
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.4),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: AppColors.wine.withOpacity(0.15),
              ),
            ),
            child: goal == null
                ? const Row(
              children: [
                Icon(
                  Icons.flag_outlined,
                  color: AppColors.wine,
                  size: 22,
                ),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Todavía no tienes una meta de ahorro activa.',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            )
                : Column(
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.wine,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.flight_takeoff,
                        color: AppColors.cardCream,
                        size: 18,
                      ),
                    ),

                    const SizedBox(width: 10),

                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'META ACTIVA',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 9,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 0.5,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            goal['nombre']?.toString() ?? 'Mi meta',
                            style: const TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),

                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '${_percentageText(goalProgress)}% listo',
                        style: const TextStyle(
                          color: AppColors.wine,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 10),

                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: goalProgress,
                    backgroundColor: AppColors.cream,
                    color: AppColors.wine,
                    minHeight: 6,
                  ),
                ),

                const SizedBox(height: 8),

                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _money(saved),
                      style: const TextStyle(
                        color: AppColors.wine,
                        fontSize: 10.5,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Meta: ${_money(target)}',
                      style: const TextStyle(
                        color: AppColors.wine,
                        fontSize: 10.5,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // CONSTRUCTOR DE FILAS DE CATEGORÍAS
  // ============================================================

  Widget _buildCategoryRow({
    required IconData icon,
    required String title,
    required String subtitle,
    required String amount,
    required String percentage,
    required double progress,
  }) {
    return Column(
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
                icon,
                color: AppColors.darkGreen,
                size: 18,
              ),
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
                      fontSize: 12.5,
                    ),
                  ),
                  const SizedBox(height: 2),
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

            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  amount,
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.w900,
                    fontSize: 12.5,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  percentage,
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ],
        ),

        const SizedBox(height: 6),

        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: progress,
            backgroundColor: AppColors.cream,
            color: AppColors.darkGreen,
            minHeight: 5,
          ),
        ),
      ],
    );
  }

  // ============================================================
  // BARRA INFERIOR DE NAVEGACIÓN
  // ============================================================

  Widget _buildBottomNavigation() {
    return Padding(
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
                    isSelected: true,
                    onTap: () {},
                  ),

                  _buildCustomNavItem(
                    icon: Icons.bar_chart_rounded,
                    label: 'Métricas',
                    isSelected: false,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const MetricsScreen(),
                        ),
                      );
                    },
                  ),

                  _buildCustomNavItem(
                    icon: Icons.account_balance_wallet_outlined,
                    label: 'Cuentas',
                    isSelected: false,
                    onTap: () {
                      Navigator.push(
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
                    onTap: _openHistoryScreen,
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(width: 8),

          GestureDetector(
            onTap: _openVoiceRecordingModal,
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
    );
  }

  // ============================================================
  // CONSTRUCTOR DE BOTONES DE NAVEGACIÓN
  // ============================================================

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
            color: isSelected
                ? AppColors.darkGreen
                : AppColors.wine,
            size: 22,
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(
              color: isSelected
                  ? AppColors.darkGreen
                  : AppColors.wine,
              fontSize: 10,
              fontWeight: isSelected
                  ? FontWeight.bold
                  : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}
