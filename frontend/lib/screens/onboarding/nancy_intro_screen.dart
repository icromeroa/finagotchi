import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/main_button.dart';
import '../../widgets/onboarding_header.dart';
import 'habits_screen.dart';

class NancyIntroScreen extends StatelessWidget {
  final String? userName;
  final String? personality;

  const NancyIntroScreen({
    super.key,
    this.userName,
    this.personality,
  });

  @override
  Widget build(BuildContext context) {
    // Si userName es null, usamos 'amig@' por seguridad
    final String nameToDisplay = userName ?? 'amig@';
    final String safePersonality = personality ?? 'amigable';

    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            OnboardingHeader(
              step: 3,
              onBack: () => Navigator.pop(context),
              onSkip: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => HabitsScreen(
                    name: nameToDisplay,
                    personality: safePersonality,
                  ),
                ),
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '¡Hola, $nameToDisplay! Soy Nancy 🐷',
                      style: const TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.w900,
                        color: AppColors.wine,
                        height: 1.2,
                      ),
                    ),
                    const SizedBox(height: 120),
                    Center(
                      child: SizedBox(
                        height: 190,
                        child: Image.asset(
                          'assets/images/nancy_inicio.png',
                          fit: BoxFit.contain,
                          errorBuilder: (context, error, stackTrace) {
                            return const Icon(Icons.pets, size: 100, color: AppColors.wine);
                          },
                        ),
                      ),
                    ),
                    const SizedBox(height: 60),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        border: Border.all(color: const Color(0xFFD7A0A9)),
                        borderRadius: BorderRadius.circular(13),
                        boxShadow: const [
                          BoxShadow(
                            color: AppColors.wine,
                            offset: Offset(0, 3),
                          ),
                        ],
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: const BoxDecoration(
                              color: AppColors.mutedPink,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.favorite_rounded,
                              color: AppColors.wine,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Vínculo Amistoso',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w900,
                                    color: AppColors.wine,
                                  ),
                                ),
                                SizedBox(height: 4),
                                Text(
                                  'Nancy recordará tu nombre y te dará ánimos todos los días cuando cumplas tus metas.',
                                  style: TextStyle(
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.darkGreen,
                                    height: 1.3,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 30),
                    MainButton(
                      text: '¡Mucho gusto, Nancy!  →',
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => HabitsScreen(
                              name: nameToDisplay,
                              personality: safePersonality,
                            ),
                          ),
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