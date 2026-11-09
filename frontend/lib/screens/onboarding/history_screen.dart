
import 'package:flutter/material.dart';
import 'package:frontend/theme/app_colors.dart';
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
  String _selectedTab = 'Todos';

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
                  // RACHA
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
                            builder: (context) => const ProfileScreen(),
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

            // CONTENIDO PRINCIPAL
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // SELECTOR DE MES
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
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
                          child: const Icon(
                            Icons.chevron_left,
                            color: AppColors.wine,
                          ),
                        ),
                        const SizedBox(width: 14),
                        Row(
                          children: const [
                            Icon(
                              Icons.calendar_month,
                              color: AppColors.wine,
                              size: 20,
                            ),
                            SizedBox(width: 6),
                            Text(
                              'Octubre 2026',
                              style: TextStyle(
                                color: AppColors.wine,
                                fontSize: 16,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(width: 14),
                        Container(
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
                          child: const Icon(
                            Icons.chevron_right,
                            color: AppColors.wine,
                          ),
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
                          _buildSummaryItem(
                            'Ingresos',
                            '+\$850.000',
                            AppColors.darkGreen,
                            Icons.north_east,
                          ),
                          Container(
                            height: 32,
                            width: 1,
                            color: AppColors.wine.withValues(alpha: 0.15),
                          ),
                          _buildSummaryItem(
                            'Gastos',
                            '-\$412.500',
                            AppColors.wine,
                            Icons.south_west,
                          ),
                          Container(
                            height: 32,
                            width: 1,
                            color: AppColors.wine.withValues(alpha: 0.15),
                          ),
                          _buildSummaryItem(
                            'Saldo',
                            '\$437.500',
                            AppColors.darkGreen,
                            null,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // BÚSQUEDA Y FILTROS
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
                              children: const [
                                Icon(
                                  Icons.search,
                                  color: AppColors.darkGreen,
                                  size: 20,
                                ),
                                SizedBox(width: 8),
                                Text(
                                  'Busca por concepto',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 13,
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
                            child: Stack(
                              alignment: Alignment.center,
                              children: [
                                const Icon(
                                  Icons.tune,
                                  color: AppColors.wine,
                                  size: 20,
                                ),
                                Positioned(
                                  top: 6,
                                  right: 6,
                                  child: Container(
                                    width: 15,
                                    height: 15,
                                    decoration: const BoxDecoration(
                                      color: AppColors.wine,
                                      shape: BoxShape.circle,
                                    ),
                                    child: const Center(
                                      child: Text(
                                        '2',
                                        style: TextStyle(
                                          color: AppColors.cardCream,
                                          fontSize: 9,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // FILTROS
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: ['Todos', 'Gastos', 'Ingresos', 'Ahorros']
                            .map((tab) {
                          bool isSelected = _selectedTab == tab;

                          return Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: ChoiceChip(
                              label: Text(tab),
                              selected: isSelected,
                              onSelected: (_) {
                                setState(() => _selectedTab = tab);
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

                    // HOY
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: const [
                        Text(
                          'Hoy',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.w900,
                            fontSize: 14.5,
                          ),
                        ),
                        Text(
                          '-\$21.000',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    _buildTransactionCard(
                      'Almuerzo corriente',
                      'Alimentación • Nequi • 1:15 PM',
                      '-\$14.000',
                      Icons.restaurant,
                      false,
                    ),
                    const SizedBox(height: 8),
                    _buildTransactionCard(
                      'Pasaje TransMilenio',
                      'Transporte • Efectivo • 07:45 AM',
                      '-\$3.000',
                      Icons.directions_bus,
                      false,
                    ),
                    _buildTransactionCard(
                      'Helado a mi mami',
                      'Familia y detalles • Efectivo',
                      '-\$4.000',
                      Icons.card_giftcard,
                      false,
                      isPending: true,
                    ),
                    const SizedBox(height: 16),

                    // AYER
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: const [
                        Text(
                          'Ayer',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.w900,
                            fontSize: 14.5,
                          ),
                        ),
                        Text(
                          '+\$145.000',
                          style: TextStyle(
                            color: AppColors.darkGreen,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    _buildTransactionCard(
                      'Mesada',
                      'Apoyo familiar • Transfiya',
                      '+\$200.000',
                      Icons.account_balance_wallet,
                      true,
                    ),
                    const SizedBox(height: 8),
                    _buildTransactionCard(
                      'Netflix',
                      'Suscripciones • Tarjeta • 10:00 PM',
                      '-\$17.000',
                      Icons.tv,
                      false,
                    ),
                    const SizedBox(height: 8),
                    _buildTransactionCard(
                      'Salida con amigos',
                      'Ocio y gustos • Daviplata',
                      '-\$38.000',
                      Icons.celebration,
                      false,
                      isEdited: true,
                    ),

                    const SizedBox(height: 16),
                    Center(
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Icon(
                            Icons.touch_app_outlined,
                            color: AppColors.darkGreen,
                            size: 14,
                          ),
                          SizedBox(width: 4),
                          Text(
                            'Mostrando octubre. Desliza para ver más.',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // BARRA INFERIOR
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
                                  builder: (context) => const HomeScreen(),
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
                                  builder: (context) => const MetricsScreen(),
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

  // RESUMEN
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
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(icon, color: color, size: 14),
              const SizedBox(width: 2),
            ],
            Text(
              amount,
              style: TextStyle(
                color: color,
                fontSize: 13.5,
                fontWeight: FontWeight.w900,
              ),
            ),
          ],
        ),
      ],
    );
  }

  // TARJETA DE TRANSACCIÓN
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
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: const [
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
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isIncome ? Icons.south_west : Icons.north_east,
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

  // NAVEGACIÓN INFERIOR
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
