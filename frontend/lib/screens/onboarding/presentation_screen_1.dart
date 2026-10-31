import 'package:flutter/material.dart';
import 'presentation_screen_2.dart';
import '../login_screen.dart';

class PresentationScreen1 extends StatelessWidget {
  const PresentationScreen1({super.key});

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
                // 1. Fondo base (sin Positioned para que el Stack tome tamaño real y funcionen los clics)
                Container(
                  width: w,
                  height: h,
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

                // Fondo rosado superior con la onda exacta.
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  height: h * 0.42,
                  child: CustomPaint(
                    painter: _WavePainter(
                      color: pink,
                      lineColor: wine,
                    ),
                  ),
                ),

                // Monedas decorativas con tu imagen coin.png
                Positioned(
                  top: h * 0.08,
                  left: w * 0.08,
                  child: const _Coin(size: 46),
                ),
                Positioned(
                  top: h * 0.045,
                  right: w * 0.28,
                  child: const _Coin(size: 46),
                ),
                Positioned(
                  top: h * 0.165,
                  right: w * 0.07,
                  child: const _Coin(size: 42),
                ),

                // Indicador de tres presentaciones (Barrita activa en el primer lugar).
                Positioned(
                  top: h * 0.385,
                  left: 0,
                  right: 0,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
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
                  left: 20,
                  right: 20,
                  child: Column(
                    children: [
                      Text(
                        'Anota tus gastos de',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: wine,
                          fontSize: w * 0.08,
                          fontWeight: FontWeight.w800,
                          height: 1.15,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'una',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: wine,
                          fontSize: w * 0.08,
                          fontWeight: FontWeight.w800,
                          height: 1.2,
                          decoration: TextDecoration.underline,
                          decorationColor: darkGreen,
                          decorationThickness: 3.5,
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
                  child: Text.rich(
                    const TextSpan(
                      style: TextStyle(
                        color: wine,
                        fontSize: 16,
                        height: 1.45,
                      ),
                      children: [
                        TextSpan(text: 'Dile a Nancy tus compras por audio en '),
                        TextSpan(
                          text: '3 segundos',
                          style: TextStyle(
                            color: darkGreen,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        TextSpan(
                          text: '. Olvídate de tablas aburridas y haz feliz a tu cerdito',
                        ),
                      ],
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),

                // Etiquetas (Presiona para hablar / Nancy feliz).
                Positioned(
                  top: h * 0.68,
                  left: 16,
                  right: 16,
                  child: Wrap(
                    alignment: WrapAlignment.center,
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF0DF),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Icon(Icons.mic, size: 20, color: darkGreen),
                            SizedBox(width: 6),
                            Text(
                              'Presiona para hablar',
                              style: TextStyle(
                                color: wine,
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF0DF),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Icon(Icons.pets, size: 20, color: Color(0xFFD86F9B)),
                            SizedBox(width: 6),
                            Text(
                              'Nancy feliz',
                              style: TextStyle(
                                color: wine,
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                // Bloque inferior organizado con un TextButton 100% interactivo
                Positioned(
                  bottom: h * 0.03,
                  left: 20,
                  right: 20,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Botón de navegación principal ("De una")
                      SizedBox(
                        height: 42,
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => const PresentationScreen2(),
                              ),
                            );
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: green,
                            foregroundColor: darkGreen,
                            elevation: 0,
                            padding: const EdgeInsets.symmetric(horizontal: 45),
                            shape: const StadiumBorder(),
                            side: const BorderSide(
                              color: darkGreen,
                              width: 1.5,
                            ),
                          ),
                          child: const Text(
                            'De una',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Enlace de inicio de sesión
                      TextButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const LoginScreen(),
                            ),
                          );
                        },
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: RichText(
                          text: const TextSpan(
                            style: TextStyle(
                              color: wine,
                              fontSize: 11.5,
                            ),
                            children: [
                              TextSpan(text: '¿Ya tienes cuenta? '),
                              TextSpan(
                                text: 'Inicia sesión',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  decoration: TextDecoration.underline,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 50),

                      // Logo inferior
                      Image.asset(
                        'assets/images/logo.png',
                        width: w * 0.22,
                        fit: BoxFit.contain,
                      ),
                    ],
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

class _Coin extends StatelessWidget {
  final double size;

  const _Coin({required this.size});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Image.asset(
        'assets/images/coin.png',
        fit: BoxFit.contain,
      ),
    );
  }
}

class _WavePainter extends CustomPainter {
  final Color color;
  final Color lineColor;

  const _WavePainter({
    required this.color,
    required this.lineColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    // Curva exacta superior para replicar el diseño limpio de Figma
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

    // Línea de contorno (stroke) idéntica a la onda
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
  bool shouldRepaint(covariant _WavePainter oldDelegate) {
    return oldDelegate.color != color || oldDelegate.lineColor != lineColor;
  }
}