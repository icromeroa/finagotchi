
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/main_button.dart';
import '../../widgets/onboarding_header.dart';
import '../home_screen.dart';

class DiagnosisScreen extends StatefulWidget {
  final String name;

  const DiagnosisScreen({
    super.key,
    required this.name,
  });

  @override
  State<DiagnosisScreen> createState() => _DiagnosisScreenState();
}

class _DiagnosisScreenState extends State<DiagnosisScreen> {
  int dailyBudget = 30000;

  String formatMoney(int value) {
    return value.toString().replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+$)'),
          (match) => '${match[1]}.',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            OnboardingHeader(
              step: 7,
              onBack: () => Navigator.pop(context),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 20, 22, 24),
                child: Column(
                  children: [
                    const Text(
                      '¡Diagnóstico Listo! 🎉',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.wine,
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      '${widget.name}, tu perfil está configurado. '
                          '¡Nancy tiene la energía al máximo!',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 11,
                      ),
                    ),
                    const SizedBox(height: 28),

                    const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.pets,
                          size: 78,
                          color: AppColors.mutedPink,
                        ),
                        SizedBox(width: 15),
                        Icon(
                          Icons.school,
                          size: 48,
                          color: AppColors.wine,
                        ),
                      ],
                    ),

                    const SizedBox(height: 22),

                    // SALUD DE NANCY
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(15),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        border: Border.all(
                          color: AppColors.darkGreen.withValues(
                            alpha: 0.45,
                          ),
                        ),
                        borderRadius: BorderRadius.circular(13),
                        boxShadow: const [
                          BoxShadow(
                            color: AppColors.darkGreen,
                            offset: Offset(0, 3),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            children: [
                              Icon(
                                Icons.monitor_heart,
                                color: AppColors.lime,
                              ),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Salud de Nancy',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                              Text(
                                '100% ÓPTIMA',
                                style: TextStyle(
                                  color: AppColors.lime,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(20),
                            child: const LinearProgressIndicator(
                              value: 1,
                              minHeight: 10,
                              backgroundColor:
                              AppColors.progressBackground,
                              valueColor: AlwaysStoppedAnimation(
                                AppColors.lime,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 25),

                    // PRESUPUESTO SUGERIDO
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        border: Border.all(
                          color: AppColors.darkGreen.withValues(
                            alpha: 0.45,
                          ),
                        ),
                        borderRadius: BorderRadius.circular(13),
                        boxShadow: const [
                          BoxShadow(
                            color: AppColors.wine,
                            offset: Offset(0, 3),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Presupuesto Sugerido',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Límite inteligente para días de clase',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 11,
                            ),
                          ),
                          const SizedBox(height: 14),

                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 10,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.cream,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: AppColors.darkGreen.withValues(
                                  alpha: 0.4,
                                ),
                              ),
                              boxShadow: const [
                                BoxShadow(
                                  color: AppColors.darkGreen,
                                  offset: Offset(0, 3),
                                ),
                              ],
                            ),
                            child: Row(
                              children: [
                                IconButton(
                                  onPressed: dailyBudget > 5000
                                      ? () => setState(
                                        () => dailyBudget -= 1000,
                                  )
                                      : null,
                                  icon: const Icon(
                                    Icons.remove_circle_outline,
                                    color: AppColors.wine,
                                  ),
                                ),
                                Expanded(
                                  child: Column(
                                    children: [
                                      Text(
                                        '\$${formatMoney(dailyBudget)}',
                                        style: const TextStyle(
                                          color: AppColors.wine,
                                          fontSize: 30,
                                          fontWeight: FontWeight.w900,
                                        ),
                                      ),
                                      const Text(
                                        'COP / día recomendados',
                                        textAlign: TextAlign.center,
                                        style: TextStyle(
                                          color: AppColors.darkGreen,
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                IconButton(
                                  onPressed: dailyBudget < 200000
                                      ? () => setState(
                                        () => dailyBudget += 1000,
                                  )
                                      : null,
                                  icon: const Icon(
                                    Icons.add_circle_outline,
                                    color: AppColors.wine,
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 14),
                          const Text(
                            'Distribución sugerida del día:',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),

                          const Wrap(
                            spacing: 6,
                            runSpacing: 6,
                            children: [
                              _BudgetChip(text: 'Transporte: \$7.000'),
                              _BudgetChip(text: 'Almuerzo: \$17.000'),
                              _BudgetChip(text: 'Snack / Tinto: \$6.000'),
                            ],
                          ),

                          const SizedBox(height: 12),
                          const Text(
                            'ⓘ Puedes ajustar este valor en cualquier '
                                'momento desde tu bóveda de ahorros.',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // BOTÓN QUE ABRE EL HOME SCREEN
                    MainButton(
                      text: '¡Comenzar mi aventura con FinaGotchi! 🚀',
                      onPressed: () {
                        Navigator.of(context).pushAndRemoveUntil(
                          MaterialPageRoute(
                            builder: (context) => const HomeScreen(),
                          ),
                              (route) => false,
                        );
                      },
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

class _BudgetChip extends StatelessWidget {
  final String text;

  const _BudgetChip({
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 9,
        vertical: 6,
      ),
      decoration: BoxDecoration(
        color: AppColors.cream,
        border: Border.all(
          color: AppColors.mutedPink,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: AppColors.wine,
          fontSize: 9,
        ),
      ),
    );
  }
}
