import 'package:flutter/material.dart';
import '../login_screen.dart';

class PresentationScreen3 extends StatelessWidget {
  const PresentationScreen3({super.key});

  static const Color wine = Color(0xFF872B54);
  static const Color cream = Color(0xFFF8E5CB);
  static const Color lime = Color(0xFFB8D833);
  static const Color darkGreen = Color(0xFF006B52);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: wine,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final h = constraints.maxHeight;
            final w = constraints.maxWidth;

            return Stack(
              clipBehavior: Clip.hardEdge,
              children: [
                // Fondo con degradado sutil vino exacto.
                Positioned.fill(
                  child: Container(
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Color(0xFF8E315C),
                          Color(0xFF872B54),
                          Color(0xFF752246),
                        ],
                        stops: [0.0, 0.5, 1.0],
                      ),
                    ),
                  ),
                ),

                // Luceros / Estrellas decorativas con tu imagen lucero.png
                Positioned(
                  top: h * 0.10,
                  left: w * 0.15,
                  child: const _Lucero(size: 36),
                ),
                Positioned(
                  top: h * 0.36,
                  right: w * 0.12,
                  child: const _Lucero(size: 28),
                ),
                Positioned(
                  top: h * 0.72,
                  left: w * 0.12,
                  child: const _Lucero(size: 24),
                ),
                Positioned(
                  top: h * 0.70,
                  right: w * 0.12,
                  child: const _Lucero(size: 32),
                ),

                // Círculo central grande con anillos concéntricos.
                Positioned(
                  top: h * 0.07,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: SizedBox(
                      width: w * 0.72,
                      height: w * 0.72,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          // Anillo exterior con borde crema translúcido
                          Container(
                            width: w * 0.72,
                            height: w * 0.72,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: cream.withOpacity(0.85),
                                width: 2.0,
                              ),
                            ),
                          ),
                          // Círculo interior beige central para la ilustración
                          Container(
                            width: w * 0.58,
                            height: w * 0.58,
                            decoration: const BoxDecoration(
                              color: cream,
                              shape: BoxShape.circle,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                // Indicador de tres presentaciones (Barrita alargada activa en la 3era posición).
                Positioned(
                  top: h * 0.46,
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
                          color: cream,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ],
                  ),
                ),

                // Título principal unificado en una sola línea fluida ("Tu alcancía evoluciona").
                Positioned(
                  top: h * 0.50,
                  left: 20,
                  right: 20,
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          'Tu alcancía ',
                          style: TextStyle(
                            color: cream,
                            fontSize: w * 0.075,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        Text(
                          'evoluciona',
                          style: TextStyle(
                            color: lime,
                            fontSize: w * 0.075,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // Descripción de dos líneas centrada.
                Positioned(
                  top: h * 0.62,
                  left: 28,
                  right: 28,
                  child: const Text(
                    'Frena antojos, cumple metas y mira a Nancy\nsubir de nivel cada vez que ahorras',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: cream,
                      fontSize: 16,
                      height: 1.4,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ),

                // Bloque inferior organizado: Botones de navegación (Sin el texto de inicio de sesión).
                Positioned(
                  bottom: h * 0.16,
                  left: 20,
                  right: 20,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Botón de retroceso circular
                      Container(
                        height: 44,
                        width: 44,
                        decoration: BoxDecoration(
                          color: cream,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: darkGreen,
                            width: 1.5,
                          ),
                        ),
                        child: IconButton(
                          padding: EdgeInsets.zero,
                          icon: const Icon(Icons.arrow_back, color: darkGreen, size: 20),
                          onPressed: () {
                            Navigator.pop(context);
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      // Botón principal de acción ("¡Arranquemos!")
                      SizedBox(
                        height: 44,
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => const LoginScreen(),
                              ),
                            );
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: lime,
                            foregroundColor: darkGreen,
                            elevation: 0,
                            padding: const EdgeInsets.symmetric(horizontal: 35),
                            shape: const StadiumBorder(),
                            side: const BorderSide(
                              color: darkGreen,
                              width: 1.5,
                            ),
                          ),
                          child: const Text(
                            '¡Arranquemos!',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // Onda inferior decorativa perfectamente posicionada al borde.
                Positioned(
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: h * 0.07,
                  child: CustomPaint(
                    painter: BottomWavePainter(),
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

class _Lucero extends StatelessWidget {
  final double size;

  const _Lucero({required this.size});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Image.asset(
        'assets/images/lucero.png',
        fit: BoxFit.contain,
      ),
    );
  }
}

class BottomWavePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final fill = Paint()
      ..color = const Color(0xFFF8E5CB)
      ..style = PaintingStyle.fill;

    final border = Paint()
      ..color = const Color(0xFFF0ADC5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final path = Path()
      ..lineTo(0, size.height * 0.5)
      ..cubicTo(
        size.width * 0.25,
        size.height * 1.2,
        size.width * 0.75,
        size.height * -0.2,
        size.width,
        size.height * 0.5,
      )
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();

    canvas.drawPath(path, fill);

    final linePath = Path()
      ..lineTo(0, size.height * 0.5)
      ..cubicTo(
        size.width * 0.25,
        size.height * 1.2,
        size.width * 0.75,
        size.height * -0.2,
        size.width,
        size.height * 0.5,
      );

    canvas.drawPath(linePath, border);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}