import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/main_button.dart';
import '../../widgets/onboarding_header.dart';
import '../../widgets/option_card.dart';
import 'challenge_two_screen.dart';

class ChallengeOneScreen extends StatefulWidget {
  final String name;
  const ChallengeOneScreen({super.key, required this.name});

  @override
  State<ChallengeOneScreen> createState() => _ChallengeOneScreenState();
}

class _ChallengeOneScreenState extends State<ChallengeOneScreen> {
  String? answer;
  final options = const [
    ('A', 'Más de \$102.000 COP'),
    ('B', 'Exactamente \$102.000 COP'),
    ('C', "Menos de \$102.000 COP"),
    ('D', 'No sé (¡Tranqui, Nancy te enseñará!)'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            OnboardingHeader(step: 4, onBack: () => Navigator.pop(context), onSkip: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ChallengeTwoScreen(name: widget.name)))),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Mini Reto #1 con Nancy 🧠', style: TextStyle(color: AppColors.wine, fontSize: 20, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 22),
                    const Row(
                      children: [
                        Expanded(child: Icon(Icons.pets, size: 75, color: AppColors.mutedPink)),
                        Expanded(child: _Bubble(text: '¡Imagina que estás guardando tu plata! ¿Qué pasará con el tiempo?')),
                      ],
                    ),
                    const SizedBox(height: 28),
                    const Text('Si guardas \$100.000 COP al 2% anual, ¿cuánto tendrás en 5 años?', style: TextStyle(color: AppColors.wine, fontSize: 16, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 18),
                    for (final option in options) ...[
                      OptionCard(title: option.$2, letter: option.$1, selected: answer == option.$1, onTap: () => setState(() => answer = option.$1)),
                      const SizedBox(height: 12),
                    ],
                    const SizedBox(height: 12),
                    _Tip(text: 'El interés compuesto genera intereses sobre los intereses ya ganados. ¡Tu dinero trabaja por ti en cada ciclo!'),
                    const SizedBox(height: 20),
                    MainButton(
                      text: '¡Genial! Siguiente reto  →',
                      onPressed: answer == null ? null : () => Navigator.push(context, MaterialPageRoute(builder: (_) => ChallengeTwoScreen(name: widget.name))),
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

class _Tip extends StatelessWidget {
  final String text;
  const _Tip({required this.text});
  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(13),
    decoration: BoxDecoration(color: AppColors.softPink, borderRadius: BorderRadius.circular(13)),
    child: Text('💗 NANCY TIP\n$text', style: const TextStyle(color: AppColors.wine, fontSize: 11, height: 1.4)),
  );
}
