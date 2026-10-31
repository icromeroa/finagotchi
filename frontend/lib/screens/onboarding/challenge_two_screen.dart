import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/main_button.dart';
import '../../widgets/onboarding_header.dart';
import '../../widgets/option_card.dart';
import 'challenge_three_screen.dart';

class ChallengeTwoScreen extends StatefulWidget {
  final String name;
  const ChallengeTwoScreen({super.key, required this.name});

  @override
  State<ChallengeTwoScreen> createState() => _ChallengeTwoScreenState();
}

class _ChallengeTwoScreenState extends State<ChallengeTwoScreen> {
  String? answer;
  final options = const [
    ('A', 'Más que hoy.'),
    ('B', 'Exactamente lo mismo.'),
    ('C', 'Menos que hoy.'),
    ('D', 'No sé (¡Tranqui, Nancy te enseñará!)'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            OnboardingHeader(step: 5, onBack: () => Navigator.pop(context), onSkip: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ChallengeThreeScreen(name: widget.name)))),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Mini Reto #2 con Nancy 🛒', style: TextStyle(color: AppColors.wine, fontSize: 20, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 22),
                    const Row(
                      children: [
                        Expanded(child: Icon(Icons.pets, size: 75, color: AppColors.mutedPink)),
                        Expanded(child: _Bubble(text: 'Cuidado con el monstruo silencioso... ¡Veamos qué tanto sabes de precios!')),
                      ],
                    ),
                    const SizedBox(height: 28),
                    const Text('Si tu cuenta bancaria rinde el 1% anual pero la inflación es del 2%, ¿cuánto podrás comprar exactamente dentro de 1 año?', style: TextStyle(color: AppColors.wine, fontSize: 16, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 18),
                    for (final option in options) ...[
                      OptionCard(title: option.$2, letter: option.$1, selected: answer == option.$1, onTap: () => setState(() => answer = option.$1)),
                      const SizedBox(height: 12),
                    ],
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(13),
                      decoration: BoxDecoration(color: AppColors.softPink, borderRadius: BorderRadius.circular(13)),
                      child: const Text('💗 NANCY TIP\nSi la inflación supera tus ganancias, tu dinero pierde poder adquisitivo. ¡Por eso es importante aprender a invertirlo inteligentemente!', style: TextStyle(color: AppColors.wine, fontSize: 11, height: 1.4)),
                    ),
                    const SizedBox(height: 20),
                    MainButton(
                      text: '¡Genial! Último reto  →',
                      onPressed: answer == null ? null : () => Navigator.push(context, MaterialPageRoute(builder: (_) => ChallengeThreeScreen(name: widget.name))),
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
