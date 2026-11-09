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
              onSkip: () => Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (_) => const HomeScreen()),
                    (route) => false,
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 10, 22, 24),
                child: Column(
                  children: [
                    const Text(
                      '¡Test Listo! 🎉',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.wine,
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 5),
                    const Text(
                      'Tu perfil está configurado a la perfección. Nancy tiene la energía al máximo.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 18),

                    // Ilustración central de Nancy con libreta
                    SizedBox(
                      height: 142,
                      child: Image.asset(
                        'assets/images/nancy_libreta 1.png',
                        fit: BoxFit.contain,
                        errorBuilder: (context, error, stackTrace) {
                          return const Icon(Icons.pets, size: 80, color: AppColors.mutedPink);
                        },
                      ),
                    ),

                    const SizedBox(height: 42),

                    // TARJETA DE PRESUPUESTO DIARIO
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        border: Border.all(
                          color: AppColors.darkGreen.withValues(alpha: 0.45),
                        ),
                        borderRadius: BorderRadius.circular(16),
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
                            'Comienza con tu presupuesto Diario',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 15,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Row(
                            children: const [
                              Icon(Icons.account_balance_wallet_outlined, size: 14, color: AppColors.wine),
                              SizedBox(width: 6),
                              Text(
                                'Límite inteligente para cada dia de clase',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 14),

                          // Selector numérico de presupuesto
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 8,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.cream,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: AppColors.darkGreen.withValues(alpha: 0.4),
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
                                      ? () => setState(() => dailyBudget -= 1000)
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
                                          fontSize: 28,
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
                                      ? () => setState(() => dailyBudget += 1000)
                                      : null,
                                  icon: const Icon(
                                    Icons.add_circle_outline,
                                    color: AppColors.wine,
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 12),

                          // Caja de dictado por voz
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            decoration: BoxDecoration(
                              color: AppColors.cream,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: AppColors.darkGreen.withValues(alpha: 0.4),
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
                                Container(
                                  padding: const EdgeInsets.all(6),
                                  decoration: const BoxDecoration(
                                    color: AppColors.wine,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(Icons.mic, color: AppColors.cream, size: 16),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: const [
                                      Text(
                                        'Mantén presionado para dictar',
                                        style: TextStyle(
                                          color: AppColors.wine,
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      SizedBox(height: 2),
                                      Text(
                                        'Ej: «Mi presupuesto diario es de 10mil».',
                                        style: TextStyle(
                                          color: AppColors.darkGreen,
                                          fontSize: 9.5,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                const Icon(Icons.graphic_eq, color: AppColors.wine, size: 24),
                              ],
                            ),
                          ),

                          const SizedBox(height: 14),
                          const Text(
                            'ⓘ Puedes ajustar este valor en cualquier momento desde tu bóveda de ahorros.',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 10,
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 22),

                    // BOTÓN PRINCIPAL
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