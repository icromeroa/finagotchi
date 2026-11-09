
import 'package:flutter/material.dart';
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
                    if (selectedTab == 0) _buildDailyView(),
                    if (selectedTab == 1) _buildWeeklyView(),
                    if (selectedTab == 2) _buildMonthlyView(),
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
        onTap: () => setState(() => selectedTab = index),
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
    String label = 'Hoy, Jueves 24 Oct';

    if (selectedTab == 1) {
      label = 'Semana 43  •  21 - 27 Oct';
    }

    if (selectedTab == 2) {
      label = 'Noviembre  •  Día 24 de 31';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.2),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.4),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.chevron_left,
              color: AppColors.wine,
              size: 18,
            ),
          ),
          Text(
            label,
            style: const TextStyle(
              color: AppColors.wine,
              fontWeight: FontWeight.bold,
              fontSize: 12.5,
            ),
          ),
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.4),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.chevron_right,
              color: AppColors.wine,
              size: 18,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDailyView() {
    return Column(
      children: [
        _buildFlowCard(
          income: '+\$40.000',
          expense: '-\$6.500',
          net: '+\$33.500',
          title: 'Flujo del Día',
        ),
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
                children: const [
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
              _buildCategoryDetailRow(
                Icons.restaurant,
                'Almuerzo U.',
                '77.8% (\$14k)',
                AppColors.wine,
              ),
              const SizedBox(height: 8),
              _buildCategoryDetailRow(
                Icons.directions_bus,
                'Transmilenio',
                '77.8% (\$14k)',
                AppColors.darkGreen,
              ),
              const SizedBox(height: 16),
              const Text(
                'DESGLOSE DE HOY',
                style: TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 8),
              _buildTransactionItem(
                'Almuerzo universidad',
                '1:15 PM • Cafetería Central',
                '-\$14.000',
                'Comida #1',
                Icons.restaurant,
              ),
              const SizedBox(height: 8),
              _buildTransactionItem(
                'Pasaje Transmilenio',
                '7:40 AM • Portal Norte',
                '-\$4.000',
                'Transporte #2',
                Icons.directions_bus,
              ),
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
        _buildFlowCard(
          income: '+\$150.000',
          expense: '-\$85.000',
          net: '+\$65.000',
          title: 'Flujo Semanal',
        ),
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
                      children: const [
                        Icon(
                          Icons.warning_amber_rounded,
                          color: AppColors.wine,
                          size: 12,
                        ),
                        SizedBox(width: 4),
                        Text(
                          'Tope: \$25k/día',
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
                children: [
                  _buildWeeklyBarColumn(
                    'L', 0.25, '\$35k',
                    isCream: true,
                    showTopLabel: false,
                  ),
                  _buildWeeklyBarColumn(
                    'M', 0.3, '\$35k',
                    isCream: true,
                    showTopLabel: false,
                  ),
                  _buildWeeklyBarColumn(
                    'M', 0.2, '\$35k',
                    isCream: true,
                    showTopLabel: false,
                  ),
                  _buildWeeklyBarColumn(
                    'J', 0.45, '\$35k',
                    isPink: true,
                    showTopLabel: true,
                  ),
                  _buildWeeklyBarColumn(
                    'V', 0.85, '\$35k',
                    isWine: true,
                    showTopLabel: true,
                    hasFlame: true,
                  ),
                  _buildWeeklyBarColumn(
                    'S', 0.55, '\$35k',
                    isPink: true,
                    showTopLabel: true,
                  ),
                  _buildWeeklyBarColumn(
                    'D', 0.38, '\$35k',
                    isLime: true,
                    showTopLabel: true,
                  ),
                ],
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
                  children: const [
                    Icon(
                      Icons.lightbulb_outline,
                      color: AppColors.wine,
                      size: 18,
                    ),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Viernes y Sábado concentraron el 52% del gasto semanal.',
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
          total: '\$85.000 COP',
          items: [
            {
              'icon': Icons.directions_bus,
              'name': 'Transporte',
              'amount': '\$35.000',
              'progress': 0.6,
            },
            {
              'icon': Icons.restaurant,
              'name': 'Alimentación',
              'amount': '\$30.000',
              'progress': 0.5,
            },
            {
              'icon': Icons.coffee_outlined,
              'name': 'Micro Gastos',
              'amount': '\$35.000',
              'progress': 0.6,
            },
            {
              'icon': Icons.local_activity_outlined,
              'name': 'Ocio',
              'amount': '\$35.000',
              'progress': 0.6,
            },
          ],
        ),
        const SizedBox(height: 14),
        _buildCompactTipCard(),
      ],
    );
  }

  Widget _buildMonthlyView() {
    return Column(
      children: [
        _buildFlowCard(
          income: '+\$680.000',
          expense: '-\$498.000',
          net: '+\$182.000',
          title: 'Flujo Consolidado',
        ),
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
                    children: const [
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
                    child: const Text(
                      '30 Días',
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
                children: const [
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
                    ' Presupuesto',
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
                      child: Stack(
                        alignment: Alignment.center,
                        children: const [
                          Icon(
                            Icons.show_chart,
                            color: AppColors.wine,
                            size: 54,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: const [
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
                  children: const [
                    Icon(
                      Icons.lightbulb_outline,
                      color: AppColors.wine,
                      size: 18,
                    ),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Picos de aceleración identificados en fines de semana (Días 5, 12, 19). En días hábiles mantienes meseta controlada.',
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
          total: '\$498.000',
          items: [
            {
              'icon': Icons.directions_bus,
              'name': 'Transporte',
              'amount': '\$204.180',
              'progress': 0.75,
            },
            {
              'icon': Icons.restaurant,
              'name': 'Alimentación',
              'amount': '\$174.300',
              'progress': 0.65,
            },
            {
              'icon': Icons.coffee_outlined,
              'name': 'Micro Gastos',
              'amount': '\$69.720',
              'progress': 0.3,
            },
            {
              'icon': Icons.local_activity_outlined,
              'name': 'Ocio',
              'amount': '\$49.800',
              'progress': 0.2,
            },
          ],
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
                  children: const [
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
        children: const [
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
