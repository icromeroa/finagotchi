import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import 'nancy_intro_screen.dart'; // Importante para conectar con la pantalla de Nancy

// =====================================================================
// 1. PANTALLA DE RESUMEN DE ETAPAS (StagesOverviewScreen)
// =====================================================================
class StagesOverviewScreen extends StatelessWidget {
  const StagesOverviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.wine),
          onPressed: () => Navigator.maybePop(context),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 10.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 10),
              const Text(
                'Tu ruta con',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 31,
                  fontWeight: FontWeight.w900,
                  color: AppColors.wine,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 4),
              Image.asset(
                'assets/images/logo.png',
                height: 34,
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) {
                  return const Text(
                    'finag·🐽·tchi',
                    style: TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.w900,
                      color: AppColors.wine,
                    ),
                  );
                },
              ),
              const SizedBox(height: 10),
              const Text(
                'Son 3 etapas. Nancy te acompaña en cada una.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 16,
                  height: 1.4,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 25),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildStageItem(
                      stepNumber: '1',
                      title: 'Diagnóstico',
                      subtitle: '28 días registrando',
                      isCompleted: true,
                      isLocked: false,
                      showTopLine: false,
                      showBottomLine: true,
                    ),
                    const SizedBox(height: 12),
                    _buildStageItem(
                      stepNumber: '2',
                      title: 'Transición',
                      subtitle: 'Metas y presupuesto',
                      isCompleted: false,
                      isLocked: false,
                      showTopLine: true,
                      showBottomLine: true,
                    ),
                    const SizedBox(height: 12),
                    _buildStageItem(
                      stepNumber: '3',
                      title: 'Seguimiento',
                      subtitle: 'Próximamente',
                      isCompleted: false,
                      isLocked: true,
                      showTopLine: true,
                      showBottomLine: false,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              const StageIndicator(activeIndex: 0),
              const SizedBox(height: 24),
              PrimaryButton(
                text: 'Continuar',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const StageDetailScreen(),
                    ),
                  );
                },
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStageItem({
    required String stepNumber,
    required String title,
    required String subtitle,
    required bool isCompleted,
    required bool isLocked,
    required bool showTopLine,
    required bool showBottomLine,
  }) {
    return Row(
      children: [
        SizedBox(
          width: 44,
          height: 72,
          child: Stack(
            alignment: Alignment.center,
            children: [
              if (showTopLine)
                Positioned(
                  top: 0,
                  bottom: 36,
                  child: Container(width: 3.0, color: AppColors.wine),
                ),
              if (showBottomLine)
                Positioned(
                  top: 36,
                  bottom: 0,
                  child: Container(width: 3.0, color: AppColors.wine),
                ),
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: isCompleted ? AppColors.wine : AppColors.cardCream,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.wine, width: 2.0),
                ),
                child: Center(
                  child: isLocked
                      ? const Icon(Icons.lock_rounded, size: 14, color: AppColors.wine)
                      : Text(
                    stepNumber,
                    style: TextStyle(
                      color: isCompleted ? AppColors.cardCream : AppColors.wine,
                      fontWeight: FontWeight.w900,
                      fontSize: 13,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.wine.withOpacity(0.25), width: 1.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w900,
                    color: AppColors.wine,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppColors.darkGreen,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

// =====================================================================
// 2. PANTALLA DE DETALLE ETAPA 1 (StageDetailScreen)
// =====================================================================
class StageDetailScreen extends StatelessWidget {
  const StageDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.wine),
          onPressed: () => Navigator.maybePop(context),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 10.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              SizedBox(
                height: 130,
                child: Image.asset(
                  'assets/images/nancy_libreta.png',
                  fit: BoxFit.contain,
                ),
              ),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Text(
                  'Etapa 1 de 3',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.w900,
                    fontSize: 11.5,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Primero, te conocemos',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  color: AppColors.wine,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Dos cosas para empezar con el pie derecho.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 20),
              Expanded(
                child: Center(
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: AppColors.wine.withOpacity(0.2), width: 1.5),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _buildFeatureRow(
                          icon: Icons.checklist_rounded,
                          text: 'Un test corto sobre tus ingresos y gastos',
                        ),
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 12),
                          child: Divider(height: 1, thickness: 1, color: Color(0xFFE8C8C0)),
                        ),
                        _buildFeatureRow(
                          icon: Icons.mic_rounded,
                          text: '28 días registrando por voz con tu FinaGotchi',
                        ),
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 12),
                          child: Divider(height: 1, thickness: 1, color: Color(0xFFE8C8C0)),
                        ),
                        _buildFeatureRow(
                          icon: Icons.star_rounded,
                          text: 'Ganas 1 punto por cada registro',
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const StageIndicator(activeIndex: 1),
              const SizedBox(height: 24),
              PrimaryButton(
                text: 'Siguiente',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const StageDetailSecondScreen(),
                    ),
                  );
                },
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureRow({required IconData icon, required String text}) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: const BoxDecoration(
            color: AppColors.cardCream,
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: AppColors.darkGreen, size: 20),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppColors.darkGreen,
              height: 1.25,
            ),
          ),
        ),
      ],
    );
  }
}

// =====================================================================
// 3. PANTALLA DE DETALLE ETAPA 2 (StageDetailSecondScreen)
// =====================================================================
class StageDetailSecondScreen extends StatelessWidget {
  const StageDetailSecondScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final Color cardGreenBg = const Color(0xFFD4E2C4);
    final Color cardGreenBorder = const Color(0xFF6B8E4E);

    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.wine),
          onPressed: () => Navigator.maybePop(context),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 10.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              SizedBox(
                height: 130,
                child: Image.asset(
                  'assets/images/nancy_libreta 1.png',
                  fit: BoxFit.contain,
                ),
              ),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Text(
                  'Etapa 2 de 3',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.w900,
                    fontSize: 11.5,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Después, armamos tu plan',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  color: AppColors.wine,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Con lo que registraste, Nancy te ayuda a decidir.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 20),
              Expanded(
                child: Center(
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
                    decoration: BoxDecoration(
                      color: cardGreenBg,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: cardGreenBorder.withOpacity(0.4), width: 1.5),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _buildFeatureRow(
                          icon: Icons.bar_chart_rounded,
                          text: 'Nancy te cuenta en qué se fue tu dinero',
                        ),
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 12),
                          child: Divider(height: 1, thickness: 1, color: Color(0xFFC2D2B0)),
                        ),
                        _buildFeatureRow(
                          icon: Icons.flag_rounded,
                          text: 'Defines tus metas con una fecha',
                        ),
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 12),
                          child: Divider(height: 1, thickness: 1, color: Color(0xFFC2D2B0)),
                        ),
                        _buildFeatureRow(
                          icon: Icons.account_balance_wallet_rounded,
                          text: 'Creamos tu presupuesto por categoría para 2 o 3 meses',
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const StageIndicator(activeIndex: 2),
              const SizedBox(height: 24),
              PrimaryButton(
                text: 'Siguiente',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const StageDetailThirdScreen(),
                    ),
                  );
                },
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureRow({required IconData icon, required String text}) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: const BoxDecoration(
            color: AppColors.cardCream,
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: AppColors.darkGreen, size: 20),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppColors.darkGreen,
              height: 1.25,
            ),
          ),
        ),
      ],
    );
  }
}

// =====================================================================
// 4. PANTALLA DE DETALLE ETAPA 3 (StageDetailThirdScreen)
// =====================================================================
class StageDetailThirdScreen extends StatelessWidget {
  const StageDetailThirdScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.wine),
          onPressed: () => Navigator.maybePop(context),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 10.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              SizedBox(
                height: 130,
                child: Image.asset(
                  'assets/images/nancy_dolar.png',
                  fit: BoxFit.contain,
                ),
              ),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Text(
                  'Etapa 3 de 3',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.w900,
                    fontSize: 11.5,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Y luego, cuidas tu presupuesto',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  color: AppColors.wine,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Esta etapa se desbloquea cuando termines las anteriores.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 20),
              Expanded(
                child: Center(
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: AppColors.darkGreen, width: 1.5),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _buildFeatureRow(
                          icon: Icons.favorite_rounded,
                          text: 'La salud de Nancy depende de cómo cumplas tu presupuesto',
                        ),
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 12),
                          child: Divider(height: 1, thickness: 1, color: Color(0xFFE8C8C0)),
                        ),
                        _buildFeatureRow(
                          icon: Icons.notifications_rounded,
                          text: 'Te avisamos si te pasas en una categoría',
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const StageIndicator(activeIndex: 3),
              const SizedBox(height: 24),
              PrimaryButton(
                text: 'Hacer test',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const NancyIntroScreen(userName: 'Helen'),
                    ),
                  );
                },
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureRow({required IconData icon, required String text}) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: const BoxDecoration(
            color: AppColors.cardCream,
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: AppColors.darkGreen, size: 20),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppColors.darkGreen,
              height: 1.25,
            ),
          ),
        ),
      ],
    );
  }
}

// =====================================================================
// WIDGETS GLOBALES UNIFICADOS
// =====================================================================
class PrimaryButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;

  const PrimaryButton({super.key, required this.text, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 48,
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.lime,
        borderRadius: BorderRadius.circular(24),
        border: const Border(
          bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
        ),
      ),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(24),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              text,
              style: const TextStyle(
                color: AppColors.darkGreen,
                fontWeight: FontWeight.w900,
                fontSize: 15,
              ),
            ),
            const SizedBox(width: 6),
            const Icon(Icons.arrow_forward, color: AppColors.darkGreen, size: 18),
          ],
        ),
      ),
    );
  }
}

class StageIndicator extends StatelessWidget {
  final int activeIndex;

  const StageIndicator({super.key, required this.activeIndex});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(4, (index) {
        bool isActive = index == activeIndex;
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 3.0),
          child: Container(
            width: isActive ? 16 : 5,
            height: 5,
            decoration: BoxDecoration(
              color: isActive ? AppColors.darkGreen : AppColors.mutedPink,
              borderRadius: BorderRadius.circular(3),
            ),
          ),
        );
      }),
    );
  }
}