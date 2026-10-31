import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/main_button.dart';
import '../../widgets/onboarding_header.dart';
import '../../widgets/option_card.dart';
import 'diagnosis_screen.dart';

class ChallengeThreeScreen extends StatefulWidget {
  final String name;
  const ChallengeThreeScreen({super.key, required this.name});

  @override
  State<ChallengeThreeScreen> createState() => _ChallengeThreeScreenState();
}

class _ChallengeThreeScreenState extends State<ChallengeThreeScreen> {
  String? answer;
  final options = const [
    ('A', 'Verdadero', 'Es más seguro concentrarlo en una sola alternativa.'),
    ('B', 'Falso', 'Es mucho más seguro repartirlo en varias empresas o fondos.'),
    ('C', 'No sé (¡Tranqui, Nancy te enseñará!)', 'Prefiero aprender más sobre diversificación financiera.'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            OnboardingHeader(step: 6, onBack: () => Navigator.pop(context), onSkip: () => Navigator.push(context, MaterialPageRoute(builder: (_) => DiagnosisScreen(name: widget.name)))),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Último Reto con Nancy 🛡️', style: TextStyle(color: AppColors.wine, fontSize: 20, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 22),
                    const Row(
                      children: [
                        Expanded(child: Icon(Icons.pets, size: 75, color: AppColors.mutedPink)),
                        Expanded(child: _Bubble(text: '¡Defendiendo tus ahorros! ¿Cómo protegemos nuestro tesoro de los riesgos del mercado?')),
                      ],
                    ),
                    const SizedBox(height: 28),
                    const Text('¿Invertir todo tu dinero en una sola empresa es más seguro que repartirlo en varias?', style: TextStyle(color: AppColors.wine, fontSize: 16, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 18),
                    for (final option in options) ...[
                      OptionCard(title: option.$2, description: option.$3, letter: option.$1, selected: answer == option.$1, onTap: () => setState(() => answer = option.$1)),
                      const SizedBox(height: 13),
                    ],
                    const SizedBox(height: 10),
                    MainButton(
                      text: 'Ver mi diagnóstico  →',
                      onPressed: answer == null ? null : () => Navigator.push(context, MaterialPageRoute(builder: (_) => DiagnosisScreen(name: widget.name))),
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

class _Bubble extends StatelessWidget {
  final String text;
  const _Bubble({required this.text});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(color: AppColors.cardCream, border: Border.all(color: AppColors.mutedPink), borderRadius: BorderRadius.circular(13)),
    child: Text(text, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.darkGreen, fontSize: 10)),
  );
}
