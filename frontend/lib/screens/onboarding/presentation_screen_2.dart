
import 'package:flutter/material.dart';
import 'presentation_screen_3.dart';

class PresentationScreen2 extends StatelessWidget {
  const PresentationScreen2({super.key});

  static const Color pink = Color(0xFFF0ADC5);
  static const Color wine = Color(0xFF872B54);
  static const Color cream = Color(0xFFF8E5CB);
  static const Color green = Color(0xFFB8D833);
  static const Color darkGreen = Color(0xFF006B52);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: cream,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final h = constraints.maxHeight;
            final w = constraints.maxWidth;

            return Stack(
              clipBehavior: Clip.hardEdge,
              children: [
                // Fondo crema general con degradado sutil.
                Positioned.fill(
                  child: Container(
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Color(0xFFF9ECE3),
                          Color(0xFFF8E5CB),
                          Color(0xFFF3D2BF),
                        ],
                        stops: [0.0, 0.6, 1.0],
                      ),
                    ),
                  ),
                ),

                // Fondo verde superior con onda.
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  height: h * 0.42,
                  child: CustomPaint(
                    painter: _WavePainter2(
                      color: green,
                      lineColor: darkGreen,
                    ),
                  ),
                ),

                // Huellas decorativas superiores.
                Positioned(
                  top: h * 0.12,
                  left: w * 0.12,
                  child: const _Huella(size: 38, angle: -0.3),
                ),
                Positioned(
                  top: h * 0.05,
                  left: w * 0.28,
                  child: const _Huella(size: 44, angle: 0.1),
                ),
                Positioned(
                  top: h * 0.09,
                  right: w * 0.22,
                  child: const _Huella(size: 40, angle: 0.2),
                ),
                Positioned(
                  top: h * 0.22,
                  right: w * 0.12,
                  child: const _Huella(size: 36, angle: -0.2),
                ),

                // Indicador: segunda presentación activa.
                Positioned(
                  top: h * 0.385,
                  left: 0,
                  right: 0,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 5,
                        height: 5,
                        decoration: const BoxDecoration(
                          color: Color(0xFFC18D9D),
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Container(
                        width: 14,
                        height: 4,
                        decoration: BoxDecoration(
                          color: wine,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      const SizedBox(width: 6),
                      Container(
                        width: 5,
                        height: 5,
                        decoration: const BoxDecoration(
                          color: Color(0xFFC18D9D),
                          shape: BoxShape.circle,
                        ),
                      ),
                    ],
                  ),
                ),

                // Título principal.
                Positioned(
                  top: h * 0.43,
                  left: 18,
                  right: 18,
                  child: Column(
                    children: [
                      Text(
                        'Cuentas claritas',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: wine,
                          fontSize: w * 0.078,
                          fontWeight: FontWeight.w800,
                          height: 1.15,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'y sin misterios',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: wine,
                          fontSize: w * 0.078,
                          fontWeight: FontWeight.w800,
                          height: 1.2,
                          decoration: TextDecoration.underline,
                          decorationColor: darkGreen,
                          decorationThickness: 3,
                        ),
                      ),
                    ],
                  ),
                ),

                // Descripción.
                Positioned(
                  top: h * 0.56,
                  left: 28,
                  right: 28,
                  child: const Text(
                    'Nancy te cuida el bolsillo pa’ que llegues sobrado a fin de mes y hagas crecer tus ahorros',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: wine,
                      fontSize: 15,
                      height: 1.4,
                    ),
                  ),
                ),

                // Etiquetas inferiores.
                Positioned(
                  top: h * 0.69,
                  left: 16,
                  right: 16,
                  child: Wrap(
                    alignment: WrapAlignment.center,
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF0DF),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.notifications_active_rounded,
                              size: 18,
                              color: darkGreen,
                            ),
                            const SizedBox(width: 6),
                            const Text(
                              'Gastos fijos',
                              style: TextStyle(
                                color: wine,
                                fontSize: 13.5,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF0DF),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.monetization_on_rounded,
                              size: 18,
                              color: Color(0xFFD86F9B),
                            ),
                            const SizedBox(width: 6),
                            const Text(
                              'Metas de ahorro',
                              style: TextStyle(
                                color: wine,
                                fontSize: 13.5,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                // Botones de navegación.
                Positioned(
                  top: h * 0.78,
                  left: 0,
                  right: 0,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      SizedBox(
                        width: 40,
                        height: 40,
                        child: OutlinedButton(
                          onPressed: () {
                            Navigator.maybePop(context);
                          },
                          style: OutlinedButton.styleFrom(
                            padding: EdgeInsets.zero,
                            foregroundColor: darkGreen,
                            backgroundColor: cream,
                            side: const BorderSide(
                              color: darkGreen,
                              width: 1.5,
                            ),
                            shape: const CircleBorder(),
                          ),
                          child: const Icon(
                            Icons.arrow_back,
                            size: 20,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      SizedBox(
                        height: 40,
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) =>
                                const PresentationScreen3(),
                              ),
                            );
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: green,
                            foregroundColor: darkGreen,
                            elevation: 0,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 24,
                            ),
                            shape: const StadiumBorder(),
                            side: const BorderSide(
                              color: darkGreen,
                              width: 1.5,
                            ),
                          ),
                          child: const Text(
                            '¡Listo, pa’ lante!',
                            style: TextStyle(
                              fontSize: 13.5,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // Logo inferior.
                Positioned(
                  bottom: h * 0.04,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: Image.asset(
                      'assets/images/logo.png',
                      width: w * 0.24,
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

// Widget auxiliar para las huellas.
class _Huella extends StatelessWidget {
  final double size;
  final double angle;

  const _Huella({
    required this.size,
    required this.angle,
  });

  @override
  Widget build(BuildContext context) {
    return Transform.rotate(
      angle: angle,
      child: SizedBox(
        width: size,
        height: size,
        child: Image.asset(
          'assets/images/huella.png',
          fit: BoxFit.contain,
          errorBuilder: (context, error, stackTrace) {
            return Icon(
              Icons.pets,
              size: size * 0.8,
              color: PresentationScreen2.wine.withValues(alpha: 0.5),
            );
          },
        ),
      ),
    );
  }
}

// Onda superior de la pantalla 2.
class _WavePainter2 extends CustomPainter {
  final Color color;
  final Color lineColor;

  const _WavePainter2({
    required this.color,
    required this.lineColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final path = Path()
      ..lineTo(0, size.height * 0.75)
      ..cubicTo(
        size.width * 0.2,
        size.height * 0.95,
        size.width * 0.4,
        size.height * 0.55,
        size.width * 0.65,
        size.height * 0.75,
      )
      ..cubicTo(
        size.width * 0.82,
        size.height * 0.88,
        size.width * 0.92,
        size.height * 0.72,
        size.width,
        size.height * 0.78,
      )
      ..lineTo(size.width, 0)
      ..close();

    canvas.drawPath(path, paint);

    final linePath = Path()
      ..lineTo(0, size.height * 0.75)
      ..cubicTo(
        size.width * 0.2,
        size.height * 0.95,
        size.width * 0.4,
        size.height * 0.55,
        size.width * 0.65,
        size.height * 0.75,
      )
      ..cubicTo(
        size.width * 0.82,
        size.height * 0.88,
        size.width * 0.92,
        size.height * 0.72,
        size.width,
        size.height * 0.78,
      );

    final linePaint = Paint()
      ..color = lineColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    canvas.drawPath(linePath, linePaint);
  }

  @override
  bool shouldRepaint(covariant _WavePainter2 oldDelegate) {
    return oldDelegate.color != color ||
        oldDelegate.lineColor != lineColor;
  }
}
