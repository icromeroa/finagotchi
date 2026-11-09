import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

class DailyBalanceScreen extends StatelessWidget {
  const DailyBalanceScreen({super.key});

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
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.check, color: AppColors.wine, size: 16),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Balance del Día',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Container(
                      width: 34,
                      height: 34,
                      decoration: const BoxDecoration(
                        color: AppColors.mutedPink,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.close, color: AppColors.wine, size: 18),
                    ),
                  ),
                ],
              ),
            ),

            // ===================================================================
            // CONTENIDO CON SCROLL
            // ===================================================================
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                child: Column(
                  children: [
                    // Badge de etapa y fecha
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink,
                        borderRadius: BorderRadius.circular(16),
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
                    const SizedBox(height: 4),
                    const Text(
                      'LUNES, 26 DE OCTUBRE',
                      style: TextStyle(
                        color: AppColors.wine,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Gráfico de porcentaje circular simulado
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: Column(
                        children: [
                          Stack(
                            alignment: Alignment.center,
                            children: [
                              const SizedBox(
                                width: 110,
                                height: 110,
                                child: CircularProgressIndicator(
                                  value: 0.84,
                                  backgroundColor: AppColors.cream,
                                  color: AppColors.lime,
                                  strokeWidth: 10,
                                ),
                              ),
                              Column(
                                children: const [
                                  Text(
                                    '84%',
                                    style: TextStyle(
                                      color: AppColors.wine,
                                      fontSize: 26,
                                      fontWeight: FontWeight.w900,
                                    ),
                                  ),
                                  Text(
                                    'EN RANGO SEGURO',
                                    style: TextStyle(
                                      color: AppColors.darkGreen,
                                      fontSize: 8.5,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),

                          // Saldo Neto del Día
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: AppColors.cream,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: AppColors.wine.withOpacity(0.1)),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: const [
                                    Text(
                                      'SALDO NETO DEL DÍA',
                                      style: TextStyle(
                                        color: AppColors.darkGreen,
                                        fontSize: 9.5,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    SizedBox(height: 2),
                                    Text(
                                      '+\$108.000 COP',
                                      style: TextStyle(
                                        color: AppColors.wine,
                                        fontSize: 20,
                                        fontWeight: FontWeight.w900,
                                      ),
                                    ),
                                  ],
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: AppColors.lime,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Row(
                                    children: const [
                                      Icon(Icons.trending_up, color: AppColors.darkGreen, size: 14),
                                      SizedBox(width: 4),
                                      Text(
                                        'Superávit',
                                        style: TextStyle(
                                          color: AppColors.darkGreen,
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 10),

                          // Ingresos y Gastos Totales
                          Row(
                            children: [
                              Expanded(
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
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: const [
                                          Text('Ingresos Totales', style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold)),
                                          Icon(Icons.arrow_upward, color: AppColors.darkGreen, size: 14),
                                        ],
                                      ),
                                      const SizedBox(height: 4),
                                      const Text('+\$150.000', style: TextStyle(color: AppColors.darkGreen, fontSize: 15, fontWeight: FontWeight.w900)),
                                      const SizedBox(height: 2),
                                      const Text('1 entrada (Nómina/Giro)', style: TextStyle(color: AppColors.darkGreen, fontSize: 9)),
                                    ],
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
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
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: const [
                                          Text('Gastos Totales', style: TextStyle(color: AppColors.wine, fontSize: 10.5, fontWeight: FontWeight.bold)),
                                          Icon(Icons.arrow_downward, color: AppColors.wine, size: 14),
                                        ],
                                      ),
                                      const SizedBox(height: 4),
                                      const Text('-\$42.000', style: TextStyle(color: AppColors.wine, fontSize: 15, fontWeight: FontWeight.w900)),
                                      const SizedBox(height: 2),
                                      const Text('4 transacciones', style: TextStyle(color: AppColors.wine, fontSize: 9)),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Análisis de Nancy Coach
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink.withOpacity(0.4),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 28,
                                height: 28,
                                decoration: const BoxDecoration(
                                  color: AppColors.wine,
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.smart_toy, color: AppColors.cardCream, size: 16),
                              ),
                              const SizedBox(width: 8),
                              const Text(
                                'Análisis de Nancy Coach',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.w900,
                                  fontSize: 13,
                                ),
                              ),
                              const Spacer(),
                              const Icon(Icons.verified_outlined, color: AppColors.wine, size: 18),
                            ],
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Diagnóstico automático sin costo',
                            style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Mantienes tus gastos hormiga bajo control. Tu racha de ahorro de 5 días sigue protegida y Nancy tiene salud óptima hoy.',
                            style: TextStyle(color: AppColors.darkGreen, fontSize: 11, height: 1.3),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Gastos por Categoría
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text(
                                'Gastos por Categoría',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.w900,
                                  fontSize: 14,
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.lime,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Text(
                                  '4 activas hoy',
                                  style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          _buildDetailCategoryRow(
                            icon: Icons.restaurant,
                            title: 'Alimentación',
                            subtitle: 'Nequi • 1:15 PM',
                            amount: '\$22.000 COP',
                            percentage: '52% del gasto',
                            statusText: 'Rango seguro',
                            metaText: 'Meta: < \$25.000',
                            progress: 0.52,
                          ),
                          const SizedBox(height: 12),
                          _buildDetailCategoryRow(
                            icon: Icons.directions_bus,
                            title: 'Transporte',
                            subtitle: 'Tarjeta • 8:40 AM',
                            amount: '\$12.000 COP',
                            percentage: '28% del gasto',
                            statusText: 'En presupuesto',
                            metaText: 'Ruta laboral',
                            progress: 0.28,
                          ),
                          const SizedBox(height: 12),
                          _buildDetailCategoryRow(
                            icon: Icons.coffee_outlined,
                            title: 'Café & Mecato',
                            subtitle: 'Efectivo • 4:10 PM',
                            amount: '\$6.000 COP',
                            percentage: '14% del gasto',
                            statusText: 'Advertencia gasto hormiga',
                            metaText: '2 snacks',
                            progress: 0.14,
                          ),
                          const SizedBox(height: 12),
                          _buildDetailCategoryRow(
                            icon: Icons.local_offer_outlined,
                            title: 'Imprevisto / Detalle',
                            subtitle: 'Nequi • 5:50 PM',
                            amount: '\$2.000 COP',
                            percentage: '6% del gasto',
                            statusText: 'Dentro de margen',
                            metaText: 'Comisión recarga',
                            progress: 0.06,
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
      ),
    );
  }

  Widget _buildDetailCategoryRow({
    required IconData icon,
    required String title,
    required String subtitle,
    required String amount,
    required String percentage,
    required String statusText,
    required String metaText,
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
              child: Icon(icon, color: AppColors.darkGreen, size: 18),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 12)),
                  const SizedBox(height: 2),
                  Text(subtitle, style: const TextStyle(color: AppColors.wine, fontSize: 10)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(amount, style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 12)),
                const SizedBox(height: 2),
                Text(percentage, style: const TextStyle(color: AppColors.darkGreen, fontSize: 10)),
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
            color: AppColors.mutedPink,
            minHeight: 5,
          ),
        ),
        const SizedBox(height: 4),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(statusText, style: const TextStyle(color: AppColors.darkGreen, fontSize: 9.5, fontWeight: FontWeight.bold)),
            Text(metaText, style: const TextStyle(color: AppColors.darkGreen, fontSize: 9.5)),
          ],
        ),
      ],
    );
  }
}