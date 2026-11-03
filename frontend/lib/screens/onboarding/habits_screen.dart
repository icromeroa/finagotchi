import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/main_button.dart';
import '../../widgets/onboarding_header.dart';
import '../../widgets/option_card.dart';
import 'challenge_one_screen.dart';

class HabitsScreen extends StatefulWidget {
  final String name;
  final String personality;
  const HabitsScreen({super.key, required this.name, required this.personality});

  @override
  State<HabitsScreen> createState() => _HabitsScreenState();
}

class _HabitsScreenState extends State<HabitsScreen> {
  String? selected;

  final options = const [
    _HabitData('De memoria o a ojo', 'Llega fin de mes con \$0 y muchas dudas sobre adónde se fue todo.', Icons.cloud_outlined),
    _HabitData('Anoto algunas cosas de vez en cuando', 'Sé más o menos cuánto me queda en la cuenta y me guío por intuición.', Icons.edit_note),
    _HabitData('Llevo un registro riguroso', 'Me apasiona ver métricas y tener control total (Excel, notas o apps).', Icons.bar_chart),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            OnboardingHeader(step: 3, onBack: () => Navigator.pop(context), onSkip: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ChallengeOneScreen(name: widget.name)))),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Hablemos de tus hábitos 💸', style: TextStyle(color: AppColors.wine, fontSize: 20, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 24),
                    const Row(
                      children: [
                        Expanded(child: Icon(Icons.pets, size: 78, color: AppColors.mutedPink)),
                        Expanded(child: _SpeechBubble(text: '¿Cómo te llevas con tus finanzas en la vida real? ¡Cero juzgar, promesa de cerdita!')),
                      ],
                    ),
                    const SizedBox(height: 30),
                    const Text('¿En tu día a día, cómo llevas el control de lo que gastas?', style: TextStyle(color: AppColors.wine, fontSize: 16, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 18),
                    for (final option in options) ...[
                      OptionCard(
                        title: option.title,
                        description: option.description,
                        icon: option.icon,
                        selected: selected == option.title,
                        onTap: () => setState(() => selected = option.title),
                      ),
                      const SizedBox(height: 13),
                    ],
                    const SizedBox(height: 6),
                    const Text('💗 ¡Tranquil@! Juntos vamos a crear un sistema que no te quite tiempo.', style: TextStyle(color: AppColors.wine, fontSize: 11)),
                    const SizedBox(height: 20),
                    MainButton(
                      text: 'Ir al reto  →',
                      onPressed: selected == null ? null : () => Navigator.push(context, MaterialPageRoute(builder: (_) => ChallengeOneScreen(name: widget.name))),
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

class _HabitData {
  final String title;
  final String description;
  final IconData icon;
  const _HabitData(this.title, this.description, this.icon);
}

class _SpeechBubble extends StatelessWidget {
  final String text;
  const _SpeechBubble({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        border: Border.all(color: const Color(0xFFD7A0A9)),
        borderRadius: BorderRadius.circular(13),
        boxShadow: const [BoxShadow(color: AppColors.wine, offset: Offset(0, 3))],
      ),
      child: Text(text, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.darkGreen, fontSize: 10)),
    );
  }
}
