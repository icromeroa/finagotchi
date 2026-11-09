
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import 'improve_metrics_wizard_screen.dart';

class ImproveMetricsScreen extends StatelessWidget {
  const ImproveMetricsScreen({super.key});

  // Navegación a cada sección del wizard
  void _openSection(BuildContext context, int step) {
    debugPrint('ABRIENDO SECCIÓN: $step');

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ImproveMetricsWizardScreen(
          initialStep: step,
        ),
      ),
    ).then((_) {
      debugPrint('SE CERRÓ LA SECCIÓN: $step');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
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
                      child: const Icon(
                        Icons.close,
                        color: AppColors.wine,
                        size: 20,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 10,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppColors.mutedPink,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: const Icon(
                            Icons.bar_chart_rounded,
                            color: AppColors.wine,
                            size: 24,
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Text(
                          'Mejora tus métricas',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 20,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: AppColors.wine.withValues(alpha: 0.15),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Nancy te conoce al 50%',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.w900,
                              fontSize: 15,
                            ),
                          ),
                          const SizedBox(height: 10),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Container(
                              height: 10,
                              color: AppColors.mutedPink,
                              child: Row(
                                children: [
                                  Expanded(
                                    flex: 50,
                                    child: Container(
                                      color: AppColors.lime,
                                    ),
                                  ),
                                  const Expanded(
                                    flex: 50,
                                    child: SizedBox(),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            '3 de 6 secciones completas',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 11.5,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),

                    _buildSectionItem(
                      icon: Icons.person_outline,
                      title: 'Sobre ti',
                      subtitle: '6 preguntas • 1 min',
                      statusText: 'Completo',
                      statusColor: AppColors.lime,
                      textColor: AppColors.darkGreen,
                      onTap: () => _openSection(context, 0),
                    ),

                    const SizedBox(height: 10),

                    _buildSectionItem(
                      icon: Icons.account_balance_wallet_outlined,
                      title: 'Tus ingresos',
                      subtitle: '6 preguntas • 1 min',
                      statusText: 'Completo',
                      statusColor: AppColors.lime,
                      textColor: AppColors.darkGreen,
                      onTap: () => _openSection(context, 1),
                    ),

                    const SizedBox(height: 10),

                    _buildSectionItem(
                      icon: Icons.shopping_bag_outlined,
                      title: 'Tus gastos y hábitos',
                      subtitle: '6 preguntas • 2 min',
                      statusText: 'Completo',
                      statusColor: AppColors.lime,
                      textColor: AppColors.darkGreen,
                      onTap: () => _openSection(context, 2),
                    ),

                    const SizedBox(height: 10),

                    _buildSectionItem(
                      icon: Icons.menu_book_outlined,
                      title: 'Cómo llevas tus cuentas',
                      subtitle: '3 preguntas • 30 s',
                      statusText: 'En progreso 2/5',
                      statusColor: AppColors.mutedPink,
                      textColor: AppColors.wine,
                      onTap: () => _openSection(context, 3),
                    ),

                    const SizedBox(height: 10),

                    _buildSectionItem(
                      icon: Icons.savings_outlined,
                      title: 'Deudas y ahorro',
                      subtitle: '5 preguntas • 1 min',
                      statusText: 'Pendiente',
                      statusColor: AppColors.cardCream,
                      textColor: AppColors.wine,
                      onTap: () => _openSection(context, 4),
                    ),

                    const SizedBox(height: 10),

                    _buildSectionItem(
                      icon: Icons.favorite_border,
                      title: 'Bienestar financiero',
                      subtitle: '2 preguntas • 30 s',
                      statusText: 'Pendiente',
                      statusColor: AppColors.cardCream,
                      textColor: AppColors.wine,
                      onTap: () => _openSection(context, 5),
                    ),

                    const SizedBox(height: 16),

                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink.withValues(alpha: 0.5),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: AppColors.wine.withValues(alpha: 0.12),
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
                              'Tus datos solo se usan para personalizar tus consejos. Puedes editarlos cuando quieras.',
                              style: TextStyle(
                                color: AppColors.wine,
                                fontSize: 11,
                                height: 1.3,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    Center(
                      child: Container(
                        height: 52,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: AppColors.lime,
                          borderRadius: BorderRadius.circular(26),
                          border: const Border(
                            bottom: BorderSide(
                              color: AppColors.darkGreen,
                              width: 3.5,
                            ),
                          ),
                        ),
                        child: InkWell(
                          onTap: () => _openSection(context, 3),
                          borderRadius: BorderRadius.circular(26),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: const [
                              Icon(
                                Icons.vpn_key_outlined,
                                color: AppColors.darkGreen,
                                size: 20,
                              ),
                              SizedBox(width: 8),
                              Text(
                                'Continuar donde quedé',
                                style: TextStyle(
                                  color: AppColors.darkGreen,
                                  fontWeight: FontWeight.w900,
                                  fontSize: 15,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 10),

                    Center(
                      child: TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text(
                          'Cancelar',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 13.5,
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
      ),
    );
  }

  Widget _buildSectionItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required String statusText,
    required Color statusColor,
    required Color textColor,
    required VoidCallback onTap,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.wine.withValues(alpha: 0.15),
        ),
      ),
      child: Material(
        type: MaterialType.transparency,
        child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 2,
        ),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.mutedPink,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            icon,
            color: AppColors.wine,
            size: 20,
          ),
        ),
        title: Text(
          title,
          style: const TextStyle(
            color: AppColors.wine,
            fontWeight: FontWeight.bold,
            fontSize: 13.5,
          ),
        ),
        subtitle: Text(
          subtitle,
          style: const TextStyle(
            color: AppColors.darkGreen,
            fontSize: 10.5,
          ),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 10,
                vertical: 4,
              ),
              decoration: BoxDecoration(
                color: statusColor,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppColors.wine.withValues(alpha: 0.1),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (statusText == 'Completo')
                    const Padding(
                      padding: EdgeInsets.only(right: 3),
                      child: Icon(
                        Icons.check,
                        color: AppColors.darkGreen,
                        size: 12,
                      ),
                    ),
                  Text(
                    statusText,
                    style: TextStyle(
                      color: textColor,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            const Icon(
              Icons.arrow_forward_ios,
              color: AppColors.wine,
              size: 14,
            ),
          ],
        ),
        ),
      ),
    );
  }
}
