import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class StreakScreen extends StatefulWidget {
  const StreakScreen({super.key});

  @override
  State<StreakScreen> createState() => _StreakScreenState();
}

class _StreakScreenState extends State<StreakScreen> {
  // Control para alternar: false = Vista 1 (Diagnóstico), true = Vista 2 (Post Diagnóstico)
  bool _isPostDiagnostic = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // Barra superior personalizada con botón Racha a la izquierda (interactivo para alternar)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () {
                      setState(() {
                        _isPostDiagnostic = !_isPostDiagnostic;
                      });
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine, width: 1.5),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Icon(Icons.local_fire_department, color: Colors.orange, size: 18),
                          SizedBox(width: 6),
                          Text(
                            'Racha',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    onPressed: () {},
                    icon: const Icon(Icons.notifications_none, color: AppColors.darkGreen, size: 26),
                  ),
                  IconButton(
                    onPressed: () {},
                    icon: const Icon(Icons.account_circle_outlined, color: AppColors.darkGreen, size: 26),
                  ),
                ],
              ),
            ),

            // Contenido dinámico que cambia entre tu vista original y la segunda vista
            Expanded(
              child: _isPostDiagnostic
                  ? _buildPostDiagnosticView()
                  : _buildOriginalDiagnosticView(),
            ),
          ],
        ),
      ),
    );
  }

  // ===================================================================
  // VISTA 1: Tu código original exacto (Puntos y racha diagnóstico)
  // ===================================================================
  Widget _buildOriginalDiagnosticView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Tarjetas superiores: Días Registrados y Días Perfectos
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.cardCream,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: AppColors.mutedPink.withValues(alpha: 0.5),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.local_fire_department, color: Colors.orange, size: 18),
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Días Registrados',
                        style: TextStyle(color: AppColors.wine, fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        '77',
                        style: TextStyle(color: AppColors.wine, fontSize: 26, fontWeight: FontWeight.w900),
                      ),
                      const Text(
                        'RACHA ACTUAL',
                        style: TextStyle(color: AppColors.darkGreen, fontSize: 9, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: const [
                          Icon(Icons.emoji_events, color: Colors.amber, size: 14),
                          SizedBox(width: 4),
                          Text(
                            'Mejor: 77',
                            style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.cardCream,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: AppColors.lime.withValues(alpha: 0.6),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.bolt, color: AppColors.darkGreen, size: 18),
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Días Perfectos',
                        style: TextStyle(color: AppColors.wine, fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        '21',
                        style: TextStyle(color: AppColors.wine, fontSize: 26, fontWeight: FontWeight.w900),
                      ),
                      const Text(
                        'RACHA ACTUAL',
                        style: TextStyle(color: AppColors.darkGreen, fontSize: 9, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: const [
                          Icon(Icons.emoji_events, color: Colors.amber, size: 14),
                          SizedBox(width: 4),
                          Text(
                            'Mejor: 21',
                            style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Diagnóstico de 4 Semanas (Calendario idéntico a la imagen)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.calendar_today, color: AppColors.wine, size: 18),
                    const SizedBox(width: 8),
                    const Text(
                      'Diagnóstico de 4 Semanas',
                      style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.lime,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        'Mes 1 • Hábitos',
                        style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                // Control del Mes
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.chevron_left, color: AppColors.wine, size: 20),
                    const SizedBox(width: 8),
                    const Text(
                      'Octubre 2026',
                      style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.lime,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        'Activo',
                        style: TextStyle(color: AppColors.darkGreen, fontSize: 9, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Icon(Icons.chevron_right, color: AppColors.wine, size: 20),
                  ],
                ),
                const SizedBox(height: 12),

                // Encabezados de días
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: ['L', 'M', 'M', 'J', 'V', 'S', 'D', 'Meta'].map((d) {
                    return Text(
                      d,
                      style: TextStyle(
                        color: d == 'Meta' ? AppColors.wine : AppColors.darkGreen,
                        fontWeight: FontWeight.bold,
                        fontSize: 11,
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 10),

                // Filas exactas según tu diseño de referencia
                _buildWeekCard(['1', '2', '3', '4', '5', '6', '7'], '7/7 🔥'),
                const SizedBox(height: 8),
                _buildWeekCard(['8', '9', '10', '11', '12', '13', '14'], '7/7 🔥'),
                const SizedBox(height: 8),
                _buildActiveWeekCard(['15', '16', '17', '18', '19', '20', '21'], 'Hoy ✨'),
                const SizedBox(height: 8),
                _buildLockedWeekCard(['22', '23', '24', '25', '26', '27', '28']),
                const SizedBox(height: 8),
                _buildLockedWeekCard(['29', '30', '31', '', '', '', '']),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Cuadro de motivación: Nancy te anima
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: const BoxDecoration(
                    color: AppColors.mutedPink,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text(
                        'Nancy te anima ✦',
                        style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                      SizedBox(height: 2),
                      Text(
                        '¡Vas volando! Estás a solo 2 días de superar la mitad del diagnóstico. Al culminar la Semana 4 desbloquearás el Piloto Automático de Ahorro.',
                        style: TextStyle(color: AppColors.darkGreen, fontSize: 11, height: 1.2),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Botón inferior "Mantén para hablar"
          Container(
            height: 52,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: AppColors.lime,
              borderRadius: BorderRadius.circular(26),
              border: const Border(bottom: BorderSide(color: AppColors.darkGreen, width: 3.5)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: const BoxDecoration(color: AppColors.darkGreen, shape: BoxShape.circle),
                  child: const Icon(Icons.mic, color: AppColors.lime, size: 20),
                ),
                const SizedBox(width: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: const [
                    Text(
                      'Mantén para hablar',
                      style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                    Text(
                      '“Almuerzo corriente 14 mil”',
                      style: TextStyle(color: AppColors.darkGreen, fontSize: 9.5),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ===================================================================
  // VISTA 2: Puntos y racha semana post diagnós (Basada en tu imagen 3)
  // ===================================================================
  Widget _buildPostDiagnosticView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // Insignia superior
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withValues(alpha: 0.4),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: const [
                Text('✨', style: TextStyle(fontSize: 12)),
                SizedBox(width: 6),
                Text(
                  'ETAPA 1 EN PROGRESO - HÁBITO EN CURSO',
                  style: TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // Títulos principales
          const Text(
            'Construyendo tus Hábitos',
            style: TextStyle(color: AppColors.wine, fontSize: 22, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 4),
          const Text(
            'Cada registro cuenta para conocer tu\nverdadero patrón de gastos.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.darkGreen, fontSize: 12),
          ),
          const SizedBox(height: 16),

          // Tarjeta de ilustración central
          Container(
            height: 130,
            width: double.infinity,
            margin: const EdgeInsets.symmetric(horizontal: 40),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.2)),
            ),
            child: Center(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppColors.cream,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.wine.withValues(alpha: 0.1)),
                    ),
                    child: Row(
                      children: const [
                        Icon(Icons.emoji_events, color: Colors.amber, size: 14),
                        SizedBox(width: 4),
                        Text('Nivel Max', style: TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                  const SizedBox(width: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppColors.lime,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: const [
                        Icon(Icons.local_fire_department, color: Colors.orange, size: 14),
                        SizedBox(width: 4),
                        Text('28 Días', style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Tarjeta Puntaje de Hábito
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'PUNTAJE DE HÁBITO',
                      style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink.withValues(alpha: 0.6),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Text(
                        '📌 Faltan 26 pts',
                        style: TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: const [
                    Text('74', style: TextStyle(color: AppColors.wine, fontSize: 28, fontWeight: FontWeight.w900)),
                    Text(' / 100 pts', style: TextStyle(color: AppColors.darkGreen, fontSize: 13, fontWeight: FontWeight.bold)),
                  ],
                ),
                const SizedBox(height: 10),
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: LinearProgressIndicator(
                    value: 0.74,
                    backgroundColor: AppColors.cream,
                    color: Colors.orange,
                    minHeight: 8,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text('🔥 6 días seguidos activos', style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
                    Text('Meta: 14 días', style: TextStyle(color: AppColors.darkGreen, fontSize: 11)),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Caja informativa: ¿Por qué necesitamos 100 puntos?
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    Icon(Icons.location_pin, color: AppColors.wine, size: 18),
                    SizedBox(width: 8),
                    Text(
                      '¿Por qué necesitamos 100 puntos?',
                      style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                const Text(
                  'Para que Nancy pueda calcular topes de gasto realistas sin hacerte pasar hambre ni restringirte innecesariamente, necesitamos completar el mes diagnóstico de tus hábitos reales.',
                  style: TextStyle(color: AppColors.darkGreen, fontSize: 11.5, height: 1.3),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.lime.withValues(alpha: 0.5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: const [
                      Icon(Icons.mic, color: AppColors.darkGreen, size: 16),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '¡Estás muy cerca! Solo unos días más de registro por voz.',
                          style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Botón inferior "Continuar registrando mis gastos"
          Container(
            width: double.infinity,
            height: 52,
            decoration: BoxDecoration(
              color: AppColors.lime,
              borderRadius: BorderRadius.circular(26),
              border: const Border(bottom: BorderSide(color: AppColors.darkGreen, width: 3.5)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: const [
                Text(
                  'Continuar registrando mis gastos',
                  style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 13),
                ),
                SizedBox(width: 6),
                Text('🚀', style: TextStyle(fontSize: 14)),
              ],
            ),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () {},
            child: const Text(
              'Ver detalles del diagnóstico',
              style: TextStyle(color: AppColors.darkGreen, fontSize: 11, decoration: TextDecoration.underline),
            ),
          ),
        ],
      ),
    );
  }

  // ===================================================================
  // Componentes auxiliares originales de tu calendario
  // ===================================================================
  Widget _buildWeekCard(List<String> days, String metaText) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.08)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          ...days.map((d) => SizedBox(
            width: 28,
            child: Column(
              children: [
                Text(d, style: const TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.w600)),
                const SizedBox(height: 3),
                const Icon(Icons.circle, color: AppColors.darkGreen, size: 6),
              ],
            ),
          )),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
            decoration: BoxDecoration(
              color: AppColors.lime,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              metaText,
              style: const TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActiveWeekCard(List<String> days, String metaText) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.08)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          ...days.map((d) {
            final isToday = d == '21';
            if (isToday) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: SizedBox(
                  width: 20,
                  child: Column(
                    children: [
                      Text(
                        d,
                        style: const TextStyle(
                          color: AppColors.wine,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 3),
                      const Icon(
                        Icons.circle,
                        color: AppColors.wine,
                        size: 6,
                      ),
                    ],
                  ),
                ),
              );
            }
            return SizedBox(
              width: 28,
              child: Column(
                children: [
                  Text(
                    d,
                    style: const TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 3),
                  const Icon(
                    Icons.circle,
                    color: AppColors.darkGreen,
                    size: 6,
                  ),
                ],
              ),
            );
          }),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
            decoration: BoxDecoration(
              color: AppColors.mutedPink,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.3)),
            ),
            child: Text(
              metaText,
              style: const TextStyle(color: AppColors.wine, fontSize: 10.5, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLockedWeekCard(List<String> days) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
      decoration: BoxDecoration(
        color: AppColors.cream.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.04)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          ...days.map((d) => SizedBox(
            width: 28,
            child: Column(
              children: [
                Text(
                  d,
                  style: TextStyle(
                    color: d.isEmpty ? Colors.transparent : AppColors.wine.withValues(alpha: 0.3),
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 3),
                Icon(
                  Icons.circle,
                  color: d.isEmpty ? Colors.transparent : AppColors.wine.withValues(alpha: 0.2),
                  size: 6,
                ),
              ],
            ),
          )),
          const SizedBox(
            width: 35,
            child: Center(
              child: Icon(Icons.lock_outline, color: AppColors.wine, size: 16),
            ),
          ),
        ],
      ),
    );
  }
}