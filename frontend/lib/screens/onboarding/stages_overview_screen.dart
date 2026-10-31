import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import 'perfil.dart'; // <--- ÚNICO AGREGADO: Importación de tu pantalla de perfil

class StagesOverviewScreen extends StatefulWidget {
  const StagesOverviewScreen({super.key});

  @override
  State<StagesOverviewScreen> createState() => _StagesOverviewScreenState();
}

class _StagesOverviewScreenState extends State<StagesOverviewScreen> {
  // 0: V04.1 Ruta general de las 3 etapas
  // 1: Etapa 1 de 3 (Primero, te conocemos)
  // 2: Etapa 2 de 3 (Después, armamos tu plan)
  // 3: Etapa 3 de 3 (Y luego, cuidas tu presupuesto)
  int currentStep = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: currentStep > 0
            ? IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.darkGreen),
          onPressed: () => setState(() => currentStep--),
        )
            : null,
      ),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 300),
                    child: _buildBody(),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildBody() {
    switch (currentStep) {
      case 0:
        return _buildRouteOverview();
      case 1:
        return _buildStageDetail(
          key: const ValueKey('stage_1'),
          badgeText: 'Etapa 1 de 3',
          badgeColor: AppColors.mutedPink.withOpacity(0.3),
          title: 'Primero, te conocemos',
          subtitle: 'Dos cosas para empezar con el pie derecho.',
          cardColor: AppColors.mutedPink.withOpacity(0.35),
          cardBorderColor: AppColors.wine,
          items: const [
            _DetailItem(
              icon: Icons.alt_route_rounded,
              text: 'Un test corto sobre tus ingresos y gastos',
            ),
            _DetailItem(
              icon: Icons.mic_none_outlined,
              text: '30 días registrando por voz con tu FinaGotchi',
            ),
            _DetailItem(
              icon: Icons.star_border_rounded,
              text: 'Ganas 1 punto por cada registro',
            ),
          ],
          indicatorIndex: 0,
          buttonText: 'Siguiente →',
          onTapNext: () => setState(() => currentStep = 2),
        );
      case 2:
        return _buildStageDetail(
          key: const ValueKey('stage_2'),
          badgeText: 'Etapa 2 de 3',
          badgeColor: AppColors.lime.withOpacity(0.4),
          title: 'Después, armamos tu plan',
          subtitle: 'Con lo que registraste, Nancy te ayuda a decidir.',
          cardColor: AppColors.lime.withOpacity(0.35),
          cardBorderColor: AppColors.darkGreen,
          items: const [
            _DetailItem(
              icon: Icons.bar_chart_rounded,
              text: 'Nancy te cuenta en qué se fue tu dinero',
            ),
            _DetailItem(
              icon: Icons.flag_outlined,
              text: 'Defines tus metas con una fecha',
            ),
            _DetailItem(
              icon: Icons.account_balance_wallet_outlined,
              text: 'Creamos tu presupuesto por categoría para 2 o 3 meses',
            ),
          ],
          indicatorIndex: 1,
          buttonText: 'Siguiente →',
          onTapNext: () => setState(() => currentStep = 3),
        );
      case 3:
        return _buildStageDetail(
          key: const ValueKey('stage_3'),
          badgeText: 'Etapa 3 de 3',
          badgeColor: AppColors.mutedPink.withOpacity(0.3),
          title: 'Y luego, cuidas tu presupuesto',
          subtitle: 'Esta etapa se desbloquea cuando termines las anteriores.',
          cardColor: AppColors.mutedPink.withOpacity(0.35),
          cardBorderColor: AppColors.darkGreen,
          items: const [
            _DetailItem(
              icon: Icons.favorite_border_rounded,
              text: 'La salud de Nancy depende de cómo cumplas tu presupuesto',
            ),
            _DetailItem(
              icon: Icons.notifications_none_outlined,
              text: 'Te avisamos si te pasas en una categoría',
            ),
          ],
          indicatorIndex: 2,
          buttonText: 'Hacer test →',
          onTapNext: () {
            // <--- CONEXIÓN EXACTA A TU PANTALLA PERFIL (WelcomeScreen) --->
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => const WelcomeScreen(),
              ),
            );
          },
        );
      default:
        return const SizedBox.shrink();
    }
  }

  // ==========================================
  // V04.1 RUTA DE LAS 3 ETAPAS
  // ==========================================
  Widget _buildRouteOverview() {
    return Column(
      key: const ValueKey('overview'),
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const SizedBox(height: 10),
        const Text(
          'Tu ruta con',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w800,
            color: AppColors.wine,
          ),
        ),
        const SizedBox(height: 4),
        Image.asset(
          'assets/images/logo.png',
          height: 26,
          fit: BoxFit.contain,
          filterQuality: FilterQuality.none,
        ),
        const SizedBox(height: 8),
        const Text(
          'Son 3 etapas. Nancy te acompaña\nen cada una.',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.darkGreen,
            fontSize: 13,
            height: 1.3,
          ),
        ),
        const SizedBox(height: 32),

        // Lista de las 3 etapas verticales conectadas
        _buildStageTile(
          number: '1',
          title: 'Diagnóstico',
          subtitle: '30 días registrando',
          isCompleted: false,
          isCurrent: true,
        ),
        _buildLineConnector(),
        _buildStageTile(
          number: '2',
          title: 'Transición',
          subtitle: 'Metas y presupuesto',
          isCompleted: false,
          isCurrent: false,
        ),
        _buildLineConnector(),
        _buildStageTile(
          number: '3🔒',
          title: 'Seguimiento',
          subtitle: 'Próximamente',
          isCompleted: false,
          isCurrent: false,
          isLocked: true,
        ),

        const SizedBox(height: 24),
        _buildDotsIndicator(0),
        const SizedBox(height: 32),

        // Botón Continuar con borde inferior
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(30),
            border: const Border(
              bottom: BorderSide(color: AppColors.darkGreen, width: 3),
            ),
          ),
          child: SizedBox(
            width: 140,
            height: 44,
            child: ElevatedButton(
              onPressed: () => setState(() => currentStep = 1),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.lime,
                foregroundColor: AppColors.darkGreen,
                elevation: 0,
                shape: const StadiumBorder(),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Text('Continuar', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  SizedBox(width: 6),
                  Icon(Icons.arrow_forward, size: 16),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildStageTile({
    required String number,
    required String title,
    required String subtitle,
    required bool isCompleted,
    required bool isCurrent,
    bool isLocked = false,
  }) {
    return Row(
      children: [
        // Círculo del número
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isCurrent ? AppColors.wine : AppColors.cardCream,
            border: Border.all(
              color: isCurrent ? AppColors.wine : AppColors.wine.withOpacity(0.4),
              width: 1.5,
            ),
          ),
          child: Center(
            child: Text(
              number,
              style: TextStyle(
                color: isCurrent ? AppColors.cream : AppColors.wine,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        ),
        const SizedBox(width: 14),
        // Tarjeta informativa con borde inferior
        Expanded(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(16),
              border: const Border(
                bottom: BorderSide(color: AppColors.wine, width: 3),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    color: AppColors.wine,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 11,
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

  Widget _buildLineConnector() {
    return Container(
      margin: const EdgeInsets.only(left: 17),
      height: 18,
      width: 2,
      color: AppColors.wine.withOpacity(0.4),
    );
  }

  // ==========================================
  // V04.2 PANTALLAS DE DETALLE DE ETAPA (1, 2 Y 3)
  // ==========================================
  Widget _buildStageDetail({
    required Key key,
    required String badgeText,
    required Color badgeColor,
    required String title,
    required String subtitle,
    required Color cardColor,
    required Color cardBorderColor,
    required List<_DetailItem> items,
    required int indicatorIndex,
    required String buttonText,
    required VoidCallback onTapNext,
  }) {
    return Column(
      key: key,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const SizedBox(height: 10),
        // Badge superior cápsula
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
          decoration: BoxDecoration(
            color: badgeColor,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            badgeText,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: AppColors.wine,
            ),
          ),
        ),
        const SizedBox(height: 12),

        Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w800,
            color: AppColors.wine,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          subtitle,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: AppColors.darkGreen,
            fontSize: 13,
            height: 1.3,
          ),
        ),
        const SizedBox(height: 28),

        // Tarjeta principal de la etapa con borde inferior grueso
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: cardColor,
            borderRadius: BorderRadius.circular(20),
            border: Border(
              bottom: BorderSide(color: cardBorderColor, width: 3),
            ),
          ),
          child: Column(
            children: items.map((item) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 14.0),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: const BoxDecoration(
                        color: AppColors.cardCream,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(item.icon, size: 18, color: AppColors.darkGreen),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Text(
                        item.text,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.darkGreen,
                          fontWeight: FontWeight.w600,
                          height: 1.25,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),

        const SizedBox(height: 28),
        _buildDotsIndicator(indicatorIndex),
        const SizedBox(height: 32),

        // Botón con borde inferior
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(30),
            border: const Border(
              bottom: BorderSide(color: AppColors.darkGreen, width: 3),
            ),
          ),
          child: SizedBox(
            width: 140,
            height: 44,
            child: ElevatedButton(
              onPressed: onTapNext,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.lime,
                foregroundColor: AppColors.darkGreen,
                elevation: 0,
                shape: const StadiumBorder(),
              ),
              child: Text(
                buttonText,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  // Indicador de 3 puntos (cápsula activa)
  Widget _buildDotsIndicator(int activeIndex) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (index) {
        final isActive = index == activeIndex;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          margin: const EdgeInsets.symmetric(horizontal: 3),
          width: isActive ? 16 : 6,
          height: 6,
          decoration: BoxDecoration(
            color: isActive ? AppColors.lime : AppColors.mutedPink.withOpacity(0.5),
            borderRadius: BorderRadius.circular(10),
            border: isActive
                ? Border.all(color: AppColors.darkGreen, width: 1)
                : null,
          ),
        );
      }),
    );
  }
}

class _DetailItem {
  final IconData icon;
  final String text;

  const _DetailItem({required this.icon, required this.text});
}