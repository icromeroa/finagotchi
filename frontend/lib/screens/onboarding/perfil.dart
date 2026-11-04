import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../login_screen.dart';
import 'habits_screen.dart'; // <--- Importamos la pantalla de hábitos

class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({super.key});

  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen> {
  final nameController = TextEditingController();

  @override
  void dispose() {
    nameController.dispose();
    super.dispose();
  }

  void continueToNext() {
    // Definimos un nombre por defecto si está vacío, o 'Irene'
    final name = nameController.text.trim().isEmpty ? 'Irene' : nameController.text.trim();

    // Navegación directa hacia HabitsScreen omitiendo la pantalla de personalidad
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => HabitsScreen(
          name: name,
          personality: 'amigable', // Valor por defecto ya que eliminamos PersonalityScreen
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.wine, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Configura a Nancy',
          style: TextStyle(
            color: AppColors.wine,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        centerTitle: false,
        actions: [
          TextButton(
            onPressed: continueToNext,
            child: const Text(
              'Skip',
              style: TextStyle(
                color: AppColors.wine,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Barra de progreso superior
              Container(
                height: 6,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withOpacity(0.25),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  children: [
                    Expanded(
                      flex: 20,
                      child: Container(
                        decoration: BoxDecoration(
                          color: AppColors.lime,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppColors.darkGreen, width: 0.5),
                        ),
                      ),
                    ),
                    const Spacer(flex: 80),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Saludo principal
              const Text(
                '¡Hola! Soy Nancy 🐷',
                style: TextStyle(
                  color: AppColors.wine,
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                ),
              ),

              const Spacer(),

              // Tarjeta inferior de Vínculo Amistoso
              Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink.withOpacity(0.35),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.favorite_border_rounded,
                      color: AppColors.wine,
                      size: 22,
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
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 14,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Nancy recordará tu nombre y te dará ánimos todos los días cuando cumplas tus metas.',
                          style: TextStyle(
                            color: AppColors.darkGreen,
                            fontSize: 11.5,
                            height: 1.25,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 36),

              // Botón principal
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(30),
                  border: const Border(
                    bottom: BorderSide(color: AppColors.darkGreen, width: 3),
                  ),
                ),
                child: SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: continueToNext,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.lime,
                      foregroundColor: AppColors.darkGreen,
                      elevation: 0,
                      shape: const StadiumBorder(),
                    ),
                    child: const Text(
                      '¡Mucho gusto, Nancy! →',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}