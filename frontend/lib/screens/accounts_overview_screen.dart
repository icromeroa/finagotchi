
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../services/api_service.dart';
import '../../services/auth_session.dart';
import 'home_screen.dart';
import 'metrics_screen.dart';
import 'accounts_overview_screen.dart';
import 'onboarding/streak_screen.dart';
import 'onboarding/notifications_screen.dart';
import 'onboarding/count_perfil.dart';
import 'onboarding/new_goal_modal.dart';
import 'onboarding/create_account_modal.dart';
import 'onboarding/history_screen.dart';

class AccountsOverviewScreen extends StatefulWidget {
  const AccountsOverviewScreen({super.key});

  @override
  State<AccountsOverviewScreen> createState() => _AccountsOverviewScreenState();
}

class _AccountsOverviewScreenState extends State<AccountsOverviewScreen> {
  bool _isCuentasSelected = true;
  List<Map<String, dynamic>> _cuentas = [];
  List<Map<String, dynamic>> _metas = [];
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargar_cuentas();
  }

  Future<void> _cargar_cuentas() async {
    final token = AuthSession.accessToken;
    if (token == null || token.isEmpty) {
      if (mounted) {
        setState(() {
          _cargando = false;
          _error = 'Inicia sesión para ver tus cuentas.';
        });
      }
      return;
    }
    try {
      final cuentas = await ApiService().getAccounts(accessToken: token);
      final metas = await ApiService().getGoals(accessToken: token);
      if (!mounted) return;
      setState(() {
        _cuentas = cuentas;
        _metas = metas;
        _cargando = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _error = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  String _dinero(num? valor) {
    final v = (valor ?? 0).toInt();
    final signo = v < 0 ? '-' : '';
    final abs = v.abs();
    final s = abs.toString().replaceAllMapped(
          RegExp(r'\B(?=(\d{3})+(?!\d))'),
          (m) => '.',
        );
    return '$signo\$$s';
  }

  IconData _icono_cuenta(String tipo) {
    return switch (tipo) {
      'efectivo' => Icons.payments_outlined,
      'billetera_digital' => Icons.phone_android_outlined,
      'tarjeta' => Icons.credit_card_outlined,
      'cuenta_ahorros' => Icons.account_balance_outlined,
      'inversion' => Icons.trending_up_outlined,
      _ => Icons.account_balance,
    };
  }

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

                  // NOTIFICACIONES
                  Container(
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
                    child: IconButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const NotificationsScreen(),
                          ),
                        );
                      },
                      icon: const Icon(
                        Icons.notifications_none,
                        color: AppColors.cardCream,
                        size: 20,
                      ),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                  const SizedBox(width: 10),

                  // PERFIL
                  Container(
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
                    child: IconButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ProfileScreen(),
                          ),
                        );
                      },
                      icon: const Icon(
                        Icons.person_outline,
                        color: AppColors.cardCream,
                        size: 20,
                      ),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                ],
              ),
            ),

            // PESTAÑAS
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 8,
              ),
              child: Container(
                height: 48,
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: AppColors.wine.withOpacity(0.15),
                  ),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: () {
                          setState(() => _isCuentasSelected = true);
                        },
                        child: Container(
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: _isCuentasSelected
                                ? AppColors.wine
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            'Cuentas',
                            style: TextStyle(
                              color: _isCuentasSelected
                                  ? AppColors.cardCream
                                  : AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ),
                    ),
                    Expanded(
                      child: GestureDetector(
                        onTap: () {
                          setState(() => _isCuentasSelected = false);
                        },
                        child: Container(
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: !_isCuentasSelected
                                ? AppColors.wine
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            'Metas de ahorro',
                            style: TextStyle(
                              color: !_isCuentasSelected
                                  ? AppColors.cardCream
                                  : AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // CONTENIDO
            Expanded(
              child: _isCuentasSelected
                  ? _buildCuentasView()
                  : _buildMetasAhorroView(),
            ),

            // BARRA INFERIOR DE NAVEGACIÓN
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
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
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
                            isSelected: true,
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
                                  builder: (context) => const HistoryScreen(),
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // BOTÓN DE VOZ
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

  // VISTA DE CUENTAS
  Widget _buildCuentasView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.5),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: AppColors.wine.withOpacity(0.12),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: const BoxDecoration(
                    color: AppColors.cardCream,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.lightbulb_outline,
                    color: AppColors.wine,
                    size: 18,
                  ),
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Nancy aprende de estas categorías para ordenar tus audios y mensajes al instante.',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 11.5,
                      height: 1.3,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          if (_cargando)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_error != null)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.mutedPink.withOpacity(0.5),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                _error!,
                style: const TextStyle(color: AppColors.wine, fontSize: 12),
              ),
            )
          else
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 1.35,
              children: [
                for (final cuenta in _cuentas)
                  _buildAccountCard(
                    icon: _icono_cuenta(
                      (cuenta['tipo_cuenta'] ?? '').toString(),
                    ),
                    title: (cuenta['nombre'] ?? '?').toString(),
                    saldo: (cuenta['saldo_actual'] as num?) ?? 0,
                    movimientos: (cuenta['num_movs'] as num?)?.toInt() ?? 0,
                    tagText: cuenta['es_sistema'] == 1 ? 'PREDET.' : 'TUYA',
                    hasTag: true,
                  ),
                if (_cuentas.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text(
                      'Sin cuentas. Crea tu primera cuenta.',
                      style: TextStyle(color: AppColors.wine, fontSize: 12),
                    ),
                  ),
                _buildCreateCard(),
              ],
            ),
        ],
      ),
    );
  }

  // VISTA DE METAS DE AHORRO
  IconData _icono_meta(String nombre) {
    final n = nombre.toLowerCase();
    if (n.contains('telé') || n.contains('tele') || n.contains('audi')) return Icons.headphones;
    if (n.contains('viaje') || n.contains('cartagena')) return Icons.flight_takeoff;
    if (n.contains('moto')) return Icons.motorcycle;
    if (n.contains('casa')) return Icons.home;
    if (n.contains('carro')) return Icons.directions_car;
    return Icons.savings;
  }

  Widget _buildMetasAhorroView() {
    final metas = _metas.where((m) => (m['estado'] ?? 'activa').toString() == 'activa' || m['estado'] == null).toList();
    final totalAhorrado = metas.fold<int>(0, (a, m) => a + ((m['ahorrado'] as num?)?.toInt() ?? 0));
    final totalMeta = metas.fold<int>(0, (a, m) => a + ((m['monto_meta'] as num?)?.toInt() ?? 0));
    final progresoGlobal = totalMeta > 0 ? totalAhorrado / totalMeta : 0.0;
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
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
                      'Has ahorrado en total',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${metas.length} metas activas',
                        style: const TextStyle(
                          color: AppColors.wine,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      _dinero(totalAhorrado),
                      style: const TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(width: 4),
                    const Text(
                      'COP',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: progresoGlobal,
                    backgroundColor: AppColors.mutedPink,
                    color: AppColors.lime,
                    minHeight: 8,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '${_dinero(totalAhorrado)} de ${_dinero(totalMeta)} meta acumulada',
                      style: const TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '${(progresoGlobal * 100).toStringAsFixed(1)}%',
                      style: const TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 11,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text(
                'Tus proyectos',
                style: TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              Text(
                'Ordenado por fecha',
                style: TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          if (_cargando)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_error != null)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.mutedPink.withOpacity(0.5),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                _error!,
                style: const TextStyle(color: AppColors.wine, fontSize: 12),
              ),
            )
          else if (metas.isEmpty)
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Todavía no tienes metas de ahorro. Crea tu primera meta.',
                style: TextStyle(color: AppColors.wine, fontSize: 12),
              ),
            )
          else
            for (final meta in metas)
              Column(children: [
                _buildProjectCard(
                  title: (meta['nombre'] ?? 'Meta').toString(),
                  subtitle: (meta['icono'] ?? meta['frecuencia_ahorro'] ?? 'Ahorro').toString(),
                  statusText: ((meta['estado_plan'] ?? meta['estado'] ?? 'activa') as String),
                  statusColor: AppColors.lime,
                  statusTextColor: AppColors.darkGreen,
                  currentAmount: _dinero((meta['ahorrado'] as num?) ?? 0),
                  targetAmount: _dinero((meta['monto_meta'] as num?) ?? 0),
                  progress: (((meta['porcentaje'] as num?) ?? 0) / 100.0).clamp(0.0, 1.0),
                  progressColor: AppColors.lime,
                  percentage: '${(meta['porcentaje'] as num?)?.toInt() ?? 0}%',
                  footerInfo: 'Meta: ${(meta['fecha_limite'] ?? '').toString().substring(0, (meta['fecha_limite'] ?? '').toString().length >= 10 ? 10 : (meta['fecha_limite'] ?? '').toString().length)} • Ahorra ${_dinero((meta['aporte_periodico'] as num?) ?? 0)}/periodo',
                  icon: _icono_meta((meta['nombre'] ?? '').toString()),
                ),
                const SizedBox(height: 12),
              ]),
          const SizedBox(height: 2),

          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.7),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(
                color: AppColors.wine.withOpacity(0.2),
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: const BoxDecoration(
                    color: AppColors.cardCream,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.military_tech,
                    color: AppColors.wine,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Racha Imparable',
                        style: TextStyle(
                          color: AppColors.wine,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Sin racha aún. Registra hoy para empezar.',
                        style: const TextStyle(
                          color: AppColors.wine,
                          fontSize: 10.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          Container(
            width: double.infinity,
            height: 50,
            decoration: BoxDecoration(
              color: AppColors.lime,
              borderRadius: BorderRadius.circular(25),
              border: Border.all(
                color: AppColors.darkGreen.withOpacity(0.3),
                width: 1.5,
              ),
            ),
            child: InkWell(
              onTap: () {
                showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (context) => const NewGoalModal(),
                );
              },
              borderRadius: BorderRadius.circular(25),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Icon(
                    Icons.add_circle_outline,
                    color: AppColors.darkGreen,
                    size: 20,
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Nueva meta de ahorro 🎯',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontWeight: FontWeight.w900,
                      fontSize: 14,
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

  // TARJETA DE PROYECTO
  Widget _buildProjectCard({
    required String title,
    required String subtitle,
    required String statusText,
    required Color statusColor,
    required Color statusTextColor,
    required String currentAmount,
    required String targetAmount,
    required double progress,
    required Color progressColor,
    required String percentage,
    required String footerInfo,
    required IconData icon,
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
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  color: AppColors.wine,
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
                        fontSize: 13.5,
                      ),
                    ),
                    const SizedBox(height: 1),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: statusColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  statusText,
                  style: TextStyle(
                    color: statusTextColor,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                currentAmount,
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 16,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                'de $targetAmount',
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 11,
                ),
              ),
              const Spacer(),
              Text(
                percentage,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontSize: 13,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: AppColors.mutedPink.withOpacity(0.4),
              color: progressColor,
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(
                Icons.calendar_today_outlined,
                color: AppColors.darkGreen,
                size: 12,
              ),
              const SizedBox(width: 6),
              Text(
                footerInfo,
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

  // TARJETAS DE CUENTAS
  Widget _buildAccountCard({
    required IconData icon,
    required String title,
    required num saldo,
    required int movimientos,
    String? tagText,
    bool hasTag = true,
  }) {
    final monto = _dinero(saldo);
    final esNegativo = saldo < 0;
    final tarjeta = Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.15),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  color: AppColors.wine,
                  size: 18,
                ),
              ),
              if (hasTag)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    tagText ?? '',
                    style: const TextStyle(
                      color: AppColors.wine,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 13.5,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              Text(
                monto,
                style: TextStyle(
                  color: esNegativo ? Colors.red[800] : AppColors.darkGreen,
                  fontWeight: FontWeight.w900,
                  fontSize: 22,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 2),
              Text(
                '$movimientos movs',
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
    return tarjeta;
  }

  // TARJETA CREAR CUENTA
  Widget _buildCreateCard() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.lime.withOpacity(0.6),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.darkGreen.withOpacity(0.2),
        ),
      ),
      child: InkWell(
        onTap: () {
          showModalBottomSheet(
            context: context,
            isScrollControlled: true,
            backgroundColor: Colors.transparent,
            builder: (context) => const CreateAccountModal(),
          );
        },
        borderRadius: BorderRadius.circular(20),
        child: Column(
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
                Icons.add,
                color: AppColors.lime,
                size: 22,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Crear',
              style: TextStyle(
                color: AppColors.darkGreen,
                fontWeight: FontWeight.w900,
                fontSize: 13.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ELEMENTO DE NAVEGACIÓN
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
