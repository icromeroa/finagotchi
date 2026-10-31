import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/main_button.dart';
import '../../widgets/onboarding_header.dart';
import '../../widgets/option_card.dart';
import 'habits_screen.dart';

class PersonalityScreen extends StatefulWidget {
  final String name;
  const PersonalityScreen({super.key, required this.name});

  @override
  State<PersonalityScreen> createState() => _PersonalityScreenState();
}

class _PersonalityScreenState extends State<PersonalityScreen> {
  String? selected;

  final options = const [
    _PersonalityData('Entusiasta', '¡Alegre y motivadora! Celebrará tus avances con fiesta, confeti y medallas.', Icons.local_fire_department, Color(0xFFF0D9E0)),
    _PersonalityData('Analítica', '¡Enfocada y detallista! Te dará datos exactos de tus gastos.', Icons.psychology_outlined, Color(0xFFEAF0D4)),
    _PersonalityData('Zen', '¡Tranquila y comprensiva! Sin presiones, a tu propio ritmo.', Icons.self_improvement, Color(0xFFF0D9E0)),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            OnboardingHeader(step: 2, onBack: () => Navigator.pop(context), onSkip: () => Navigator.push(context, MaterialPageRoute(builder: (_) => HabitsScreen(name: widget.name, personality: selected ?? 'Analítica')))),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Elige mi personalidad ✨', style: const TextStyle(color: AppColors.wine, fontSize: 21, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 5),
                    Text('Definirá cómo reaccionamos juntos a tus finanzas diarias.', style: const TextStyle(color: AppColors.darkGreen, fontSize: 14, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 25),
                    const Center(child: Icon(Icons.pets, size: 82, color: AppColors.mutedPink)),
                    const SizedBox(height: 20),
                    for (final option in options) ...[
                        OptionCard(
                        title: option.name,
                        description: option.description,
                        icon: option.icon,
                        selected: selected == option.name,
                        onTap: () => setState(() => selected = option.name),
                      ),
                      const SizedBox(height: 13),
                    ],
                    const SizedBox(height: 10),
                    MainButton(
                      text: 'Confirmar  →',
                      onPressed: selected == null ? null : () => Navigator.push(context, MaterialPageRoute(builder: (_) => HabitsScreen(name: widget.name, personality: selected!))),
                    ),
                    const SizedBox(height: 12),
                    const Center(child: Text('Puedes modificar el temperamento de Nancy en Ajustes cuando quieras.', textAlign: TextAlign.center, style: TextStyle(color: AppColors.wine, fontSize: 11))),
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

class _PersonalityData {
  final String name;
  final String description;
  final IconData icon;
  final Color color;
  const _PersonalityData(this.name, this.description, this.icon, this.color);
}
