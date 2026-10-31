import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int selectedTab = 0;
  int dailyBudget = 10000;
  int spent = 2500;
  bool isRecording = false;

  @override
  Widget build(BuildContext context) {
    final available = dailyBudget - spent;
    final progress = dailyBudget > 0
        ? (spent / dailyBudget).clamp(0.0, 1.0)
        : 0.0;

    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // CONTENIDO PRINCIPAL SCROLLEABLE
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 10, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. BARRA SUPERIOR (Racha, Notificaciones, Perfil)
                    Row(
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: AppColors.cardCream,
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: AppColors.wine, width: 1.5),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: const [
                                  Icon(Icons.local_fire_department, color: Colors.orange, size: 18),
                                  SizedBox(width: 4),
                                  Text(
                                    'Racha',
                                    style: TextStyle(
                                      color: AppColors.wine,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 3),
                            const Padding(
                              padding: EdgeInsets.only(left: 2),
                              child: Text(
                                '● Registra hoy para mantenerla',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontSize: 9.5,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const Spacer(),
                        IconButton(
                          onPressed: () => _message('Aquí aparecerán tus notificaciones.'),
                          icon: const Icon(
                            Icons.notifications_none,
                            color: AppColors.darkGreen,
                            size: 26,
                          ),
                        ),
                        IconButton(
                          onPressed: () => _message('Tu perfil estará disponible aquí.'),
                          icon: const Icon(
                            Icons.account_circle_outlined,
                            color: AppColors.darkGreen,
                            size: 26,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 12),

                    // 2. GLOBO DE DIÁLOGO DE NANCY
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppColors.cardCream,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(color: AppColors.wine, width: 1.5),
                        ),
                        child: const Text(
                          '¿Qué tal si me cuentas tu primer gasto?',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),

                    // 3. HABITACIÓN CLÁSICA DE FINAGOTCHI
                    SizedBox(
                      height: 260,
                      width: double.infinity,
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(18),
                        child: Image.asset(
                          'assets/images/Habitacion_clasica.png',
                          fit: BoxFit.contain,
                          errorBuilder: (context, error, stackTrace) {
                            return Container(
                              color: AppColors.cardCream,
                              alignment: Alignment.center,
                              padding: const EdgeInsets.all(16),
                              child: const Text(
                                'No se pudo cargar la habitación.',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: AppColors.wine),
                              ),
                            );
                          },
                        ),
                      ),
                    ),

                    // ESPACIO AMPLIADO (Aprox 1 cm de respiro para que no quede apiñado)
                    const SizedBox(height: 24),

                    // 4. BOTÓN FLOTANTE "Finaliza tu día"
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFCC70),
                          borderRadius: BorderRadius.circular(24),
                          border: const Border(
                            bottom: BorderSide(color: AppColors.wine, width: 3.5),
                          ),
                        ),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Text(
                              'Finaliza tu día',
                              style: TextStyle(
                                color: AppColors.wine,
                                fontWeight: FontWeight.w800,
                                fontSize: 13.5,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              '“Almuerzo corriente 14 mil”',
                              style: TextStyle(
                                color: AppColors.wine,
                                fontSize: 11,
                                fontStyle: FontStyle.italic,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    // ESPACIO AMPLIADO ENTRE BOTONES
                    const SizedBox(height: 16),

                    // 5. BOTONES DE ACCIÓN (Mantén para hablar + Escribir)
                    Row(
                      children: [
                        Expanded(
                          flex: 65,
                          child: GestureDetector(
                            onLongPressStart: (_) => setState(() => isRecording = true),
                            onLongPressEnd: (_) {
                              setState(() => isRecording = false);
                              _message('Registro de voz conectado.');
                            },
                            child: Container(
                              height: 52,
                              padding: const EdgeInsets.symmetric(horizontal: 8),
                              decoration: BoxDecoration(
                                color: isRecording ? AppColors.mutedPink : AppColors.lime,
                                borderRadius: BorderRadius.circular(26),
                                border: const Border(
                                  bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
                                ),
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    width: 36,
                                    height: 36,
                                    decoration: const BoxDecoration(
                                      color: AppColors.darkGreen,
                                      shape: BoxShape.circle,
                                    ),
                                    child: const Icon(Icons.mic, color: AppColors.lime, size: 20),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: const [
                                        Text(
                                          'Mantén para hablar',
                                          style: TextStyle(
                                            color: AppColors.darkGreen,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 12,
                                          ),
                                        ),
                                        Text(
                                          '“Almuerzo corriente 14 mil”',
                                          style: TextStyle(
                                            color: AppColors.darkGreen,
                                            fontSize: 9.5,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          flex: 35,
                          child: InkWell(
                            onTap: () => _message('Abrir teclado para escribir.'),
                            borderRadius: BorderRadius.circular(26),
                            child: Container(
                              height: 52,
                              decoration: BoxDecoration(
                                color: AppColors.mutedPink,
                                borderRadius: BorderRadius.circular(26),
                                border: const Border(
                                  bottom: BorderSide(color: AppColors.wine, width: 3.5),
                                ),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: const [
                                  Icon(Icons.edit_note, color: AppColors.wine, size: 20),
                                  SizedBox(width: 4),
                                  Text(
                                    'Escribir',
                                    style: TextStyle(
                                      color: AppColors.wine,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),

                    // ESPACIO AMPLIADO ANTES DE LAS TARJETAS
                    const SizedBox(height: 20),

                    // 6. TARJETA DE PRESUPUESTO (Cupo Diario Libre)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.darkGreen.withOpacity(0.2)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.account_balance_wallet, color: AppColors.wine, size: 20),
                              const SizedBox(width: 8),
                              const Expanded(
                                child: Text(
                                  'Cupo Diario Libre',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.lime,
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(color: AppColors.darkGreen, width: 1),
                                ),
                                child: const Text(
                                  'seguro',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          const Text(
                            'Disponible hoy',
                            style: TextStyle(color: AppColors.darkGreen, fontSize: 10),
                          ),
                          const SizedBox(height: 4),
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Expanded(
                                child: Text(
                                  _money(available),
                                  style: const TextStyle(
                                    color: AppColors.wine,
                                    fontSize: 28,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  const Text(
                                    'Tope máximo',
                                    style: TextStyle(color: AppColors.darkGreen, fontSize: 10),
                                  ),
                                  Text(
                                    'de ${_money(dailyBudget)}',
                                    style: const TextStyle(
                                      color: AppColors.wine,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(20),
                            child: LinearProgressIndicator(
                              value: progress,
                              minHeight: 8,
                              backgroundColor: AppColors.cream,
                              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.lime),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                '${_money(spent)} gastado',
                                style: const TextStyle(color: AppColors.darkGreen, fontSize: 10),
                              ),
                              Text(
                                '${((available / (dailyBudget == 0 ? 1 : dailyBudget)) * 100).round()}% disponible',
                                style: const TextStyle(color: AppColors.darkGreen, fontSize: 10),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),

                    // 7. TARJETA DE DIAGNÓSTICO (Etapa 1 de 3)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.darkGreen.withOpacity(0.2)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.flag_outlined, color: AppColors.wine, size: 18),
                              const SizedBox(width: 6),
                              const Text(
                                'Diagnóstico',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                              const Spacer(),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: AppColors.mutedPink.withOpacity(0.4),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: const Text(
                                  'Etapa 1 de 3',
                                  style: TextStyle(color: AppColors.wine, fontSize: 9, fontWeight: FontWeight.bold),
                                ),
                              ),
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: AppColors.lime.withOpacity(0.6),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: const Text(
                                  'Día 1 de 30',
                                  style: TextStyle(color: AppColors.darkGreen, fontSize: 9, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(20),
                            child: LinearProgressIndicator(
                              value: 0.0,
                              minHeight: 6,
                              backgroundColor: AppColors.cream,
                              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.darkGreen),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: const [
                              Text('0 de 60 registros', style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                              Text('0 puntos ★', style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),

                    // 8. ÚLTIMOS MOVIMIENTOS
                    const Text(
                      'Últimos movimientos',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine.withOpacity(0.3)),
                      ),
                      child: Column(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: AppColors.mutedPink.withOpacity(0.4),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.mic, color: AppColors.wine, size: 22),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Aún no hay registros',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(height: 2),
                          const Text(
                            'Mantén presionado el botón y cuéntame tu primer gasto.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: AppColors.darkGreen, fontSize: 11),
                          ),
                          const SizedBox(height: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppColors.cream,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Text(
                              '⚡ Demora menos de 3 segundos',
                              style: TextStyle(color: AppColors.wine, fontSize: 9, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // 9. NAVEGACIÓN INFERIOR
            Padding(
              padding: const EdgeInsets.fromLTRB(22, 0, 22, 12),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      decoration: BoxDecoration(
                        color: AppColors.cream,
                        border: Border.all(color: AppColors.darkGreen, width: 1.5),
                        borderRadius: BorderRadius.circular(35),
                        boxShadow: const [
                          BoxShadow(color: AppColors.darkGreen, offset: Offset(0, 3)),
                        ],
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _navItem(Icons.home_outlined, 'Inicio', 0),
                          _navItem(Icons.bar_chart, 'Métricas', 1),
                          _navItem(Icons.manage_search, 'Historial', 2),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  // BÓVEDA DE AHORROS
                  InkWell(
                    onTap: () => _message('Aquí estará tu bóveda de ahorros.'),
                    customBorder: const CircleBorder(),
                    child: Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: AppColors.lime,
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.darkGreen, width: 1.5),
                        boxShadow: const [
                          BoxShadow(color: AppColors.darkGreen, offset: Offset(0, 3)),
                        ],
                      ),
                      child: const Icon(Icons.savings, color: AppColors.darkGreen, size: 26),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ELEMENTOS DE NAVEGACIÓN
  Widget _navItem(IconData icon, String label, int index) {
    final active = selectedTab == index;

    return InkWell(
      onTap: () {
        setState(() => selectedTab = index);
        if (index != 0) {
          _message('$label estará disponible próximamente.');
        }
      },
      borderRadius: BorderRadius.circular(15),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: active ? AppColors.darkGreen : AppColors.wine,
              size: 26,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                color: AppColors.darkGreen,
                fontSize: 9,
                fontWeight: active ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // FORMATO DE DINERO
  String _money(int value) {
    final digits = value.abs().toString();
    final formatted = digits.replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+$)'),
          (match) => '${match[1]}.',
    );
    return '${value < 0 ? '-' : ''}\$$formatted';
  }

  // MENSAJES TEMPORALES
  void _message(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}