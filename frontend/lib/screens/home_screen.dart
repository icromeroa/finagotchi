import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // ===================================================================
            // BARRA SUPERIOR
            // ===================================================================
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Botón Racha y subtítulo exacto
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                        decoration: BoxDecoration(
                          color: AppColors.cardCream,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: AppColors.wine, width: 1.5),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Icon(Icons.local_fire_department, color: Colors.orange, size: 18),
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
                  const Spacer(),
                  // Iconos superiores (Notificaciones y Perfil en verde oscuro)
                  IconButton(
                    onPressed: () {},
                    icon: const Icon(Icons.notifications_none, color: AppColors.darkGreen, size: 26),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                  const SizedBox(width: 14),
                  IconButton(
                    onPressed: () {},
                    icon: const Icon(Icons.account_circle_outlined, color: AppColors.darkGreen, size: 26),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),

            // ===================================================================
            // CONTENIDO CON SCROLL
            // ===================================================================
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                child: Column(
                  children: [
                    // Barra de Etapa 1 superior con progreso (0/100)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      margin: const EdgeInsets.only(bottom: 10),
                      decoration: BoxDecoration(
                        color: AppColors.lime.withValues(alpha: 0.5),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppColors.darkGreen.withValues(alpha: 0.15), width: 1),
                      ),
                      child: Row(
                        children: [
                          const Text(
                            'Etapa 1 de 3: Diagnóstico • Día 1 de 28',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const Spacer(),
                          SizedBox(
                            width: 45,
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: const LinearProgressIndicator(
                                value: 0.0,
                                backgroundColor: AppColors.cream,
                                color: AppColors.darkGreen,
                                minHeight: 5,
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),
                          const Text(
                            '0/100',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Globo de diálogo de Nancy con el pico hacia abajo
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine, width: 1.5),
                      ),
                      child: const Text(
                        '¿Qué tal si me cuentas tu primer gasto?',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: AppColors.wine,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Tarjeta central grande con borde y alcancía de cerdito
                    Container(
                      height: 220,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink.withValues(alpha: 0.3),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: AppColors.wine.withValues(alpha: 0.4),
                          width: 1.5,
                          style: BorderStyle.solid,
                        ),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.pets, color: AppColors.wine, size: 40),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Botón intermedio "Finaliza tu día"
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.orange.shade300,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine, width: 1.5),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Text(
                            'Finaliza tu día',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                          Text(
                            '“Almuerzo corriente 14 mil”',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Botones inferiores de entrada (Voz y Escribir)
                    Row(
                      children: [
                        Expanded(
                          flex: 3,
                          child: Container(
                            height: 50,
                            padding: const EdgeInsets.symmetric(horizontal: 10),
                            decoration: BoxDecoration(
                              color: AppColors.lime,
                              borderRadius: BorderRadius.circular(25),
                              border: const Border(
                                bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
                                top: BorderSide(color: Colors.transparent),
                                left: BorderSide(color: Colors.transparent),
                                right: BorderSide(color: Colors.transparent),
                              ),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 34,
                                  height: 34,
                                  decoration: const BoxDecoration(
                                    color: AppColors.darkGreen,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(Icons.mic, color: AppColors.lime, size: 18),
                                ),
                                const SizedBox(width: 8),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: const [
                                    Text(
                                      'Mantén para hablar',
                                      style: TextStyle(
                                        color: AppColors.darkGreen,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 11.5,
                                      ),
                                    ),
                                    Text(
                                      '“Almuerzo corriente 14 mil”',
                                      style: TextStyle(
                                        color: AppColors.darkGreen,
                                        fontSize: 9,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 2,
                          child: Container(
                            height: 50,
                            decoration: BoxDecoration(
                              color: AppColors.mutedPink,
                              borderRadius: BorderRadius.circular(25),
                              border: const Border(
                                bottom: BorderSide(color: AppColors.wine, width: 3.5),
                                top: BorderSide(color: Colors.transparent),
                                left: BorderSide(color: Colors.transparent),
                                right: BorderSide(color: Colors.transparent),
                              ),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: const [
                                Icon(Icons.edit_outlined, color: AppColors.wine, size: 18),
                                SizedBox(width: 6),
                                Text(
                                  'Escribir',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // Tarjeta Cupo Diario Libre
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: const [
                                  Icon(Icons.account_balance_wallet_outlined, color: AppColors.wine, size: 18),
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
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.lime,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Text(
                                  'seguro',
                                  style: TextStyle(
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
                            children: const [
                              Text(
                                '\$7.500',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontSize: 26,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                              Spacer(),
                              Text(
                                'Tope máximo\nde \$10.000',
                                textAlign: TextAlign.right,
                                style: TextStyle(
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
                            child: const LinearProgressIndicator(
                              value: 0.75,
                              backgroundColor: AppColors.cream,
                              color: AppColors.darkGreen,
                              minHeight: 8,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: const [
                              Text(
                                '\$2.500 gastado',
                                style: TextStyle(
                                  color: AppColors.darkGreen,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                '40% disponible',
                                style: TextStyle(
                                  color: AppColors.darkGreen,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Sección Gastos por Categoría
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: const [
                                  Icon(Icons.pie_chart_outline, color: AppColors.darkGreen, size: 18),
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
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.lime,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Text(
                                  '3 activas hoy',
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

                          // Categoría 1: Alimentación
                          _buildCategoryRow(
                            icon: Icons.restaurant,
                            title: 'Alimentación',
                            subtitle: 'Nequi • 1:15 PM',
                            amount: '\$22.000 COP',
                            percentage: '52% del gasto',
                            progress: 0.52,
                          ),
                          const SizedBox(height: 10),

                          // Categoría 2: Transporte
                          _buildCategoryRow(
                            icon: Icons.directions_bus,
                            title: 'Transporte',
                            subtitle: 'Tarjeta • 8:40 AM',
                            amount: '\$12.000 COP',
                            percentage: '28% del gasto',
                            progress: 0.28,
                          ),
                          const SizedBox(height: 10),

                          // Categoría 3: Café & Mecato
                          _buildCategoryRow(
                            icon: Icons.coffee_outlined,
                            title: 'Café & Mecato',
                            subtitle: 'Efectivo • 4:10 PM',
                            amount: '\$6.000 COP',
                            percentage: '14% del gasto',
                            progress: 0.14,
                          ),
                          const SizedBox(height: 12),

                          // Meta Activa Interna
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: AppColors.mutedPink.withValues(alpha: 0.3),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Row(
                                      children: const [
                                        Icon(Icons.flight_takeoff, color: AppColors.wine, size: 14),
                                        SizedBox(width: 6),
                                        Text(
                                          'META ACTIVA',
                                          style: TextStyle(
                                            color: AppColors.wine,
                                            fontSize: 9,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ],
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: AppColors.cardCream,
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                      child: const Text(
                                        '25% listo',
                                        style: TextStyle(
                                          color: AppColors.wine,
                                          fontSize: 9.5,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Viaje a Cartagena',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12.5,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(6),
                                  child: const LinearProgressIndicator(
                                    value: 0.25,
                                    backgroundColor: AppColors.cream,
                                    color: AppColors.wine,
                                    minHeight: 6,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: const [
                                    Text(
                                      '\$200.000 COP',
                                      style: TextStyle(
                                        color: AppColors.wine,
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    Text(
                                      'Meta: \$800.000 COP',
                                      style: TextStyle(
                                        color: AppColors.darkGreen,
                                        fontSize: 10,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ===================================================================
            // BARRA INFERIOR DE NAVEGACIÓN
            // ===================================================================
            Container(
              margin: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: AppColors.darkGreen, width: 2),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(icon: Icons.home, label: 'Inicio', isSelected: true),
                  _buildNavItem(icon: Icons.bar_chart, label: 'Métricas', isSelected: false),
                  _buildNavItem(icon: Icons.account_balance_wallet_outlined, label: 'Cuentas', isSelected: false),
                  _buildNavItem(icon: Icons.assignment_outlined, label: 'Historial', isSelected: false),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Widget auxiliar para las filas de categorías individuales
  Widget _buildCategoryRow({
    required IconData icon,
    required String title,
    required String subtitle,
    required String amount,
    required String percentage,
    required double progress,
  }) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.08)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: AppColors.wine, size: 18),
              ),
              const SizedBox(width: 10),
              Column(
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
                  Text(
                    subtitle,
                    style: const TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
              const Spacer(),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    amount,
                    style: const TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 12.5,
                    ),
                  ),
                  Text(
                    percentage,
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
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: AppColors.mutedPink.withValues(alpha: 0.4),
              color: AppColors.lime,
              minHeight: 6,
            ),
          ),
        ],
      ),
    );
  }

  // Widget auxiliar para los elementos de la barra de navegación inferior
  Widget _buildNavItem({required IconData icon, required String label, required bool isSelected}) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          color: isSelected ? AppColors.darkGreen : AppColors.darkGreen.withValues(alpha: 0.5),
          size: 22,
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(
            color: isSelected ? AppColors.darkGreen : AppColors.darkGreen.withValues(alpha: 0.5),
            fontSize: 10,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ],
    );
  }
}