import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/voice_recording_modal.dart';
import '../../widgets/manual_register_modal.dart';
import 'count_perfil.dart';          // Tu pantalla de perfil existente
import 'notifications_screen.dart';   // <--- Importa aquí tu nueva pantalla de notificaciones

class StreakScreen extends StatelessWidget {
  const StreakScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // ===================================================================
            // BARRA SUPERIOR CON BOTONES ACTIVOS
            // ===================================================================
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
                    decoration: BoxDecoration(
                      color: Colors.orange.shade300,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: AppColors.wine.withOpacity(0.3), width: 1.2),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: const [
                        Icon(Icons.local_fire_department, color: AppColors.wine, size: 20),
                        SizedBox(width: 6),
                        Text(
                          'Racha',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  // ===================================================
                  // BOTÓN DE NOTIFICACIONES (Conectado a NotificationsScreen)
                  // ===================================================
                  Container(
                    width: 44,
                    height: 44,
                    decoration: const BoxDecoration(
                      color: AppColors.darkGreen,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const NotificationsScreen(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.notifications_none, color: AppColors.cream, size: 22),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                  const SizedBox(width: 12),
                  // ===================================================
                  // BOTÓN DE PERFIL (Conectado a ProfileScreen)
                  // ===================================================
                  Container(
                    width: 44,
                    height: 44,
                    decoration: const BoxDecoration(
                      color: AppColors.darkGreen,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ProfileScreen(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.person_outline, color: AppColors.cream, size: 22),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                ],
              ),
            ),

            // ===================================================================
            // CONTENIDO CON SCROLL
            // ===================================================================
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Tarjetas Superiores: Racha Activa y Meta Mes
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AppColors.cardCream,
                              borderRadius: BorderRadius.circular(24),
                              border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: AppColors.mutedPink,
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: const Text(
                                        'Etapa 1',
                                        style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                    const Icon(Icons.local_fire_department, color: AppColors.wine, size: 20),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                const Text(
                                  'RACHA ACTIVA',
                                  style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 2),
                                const Text(
                                  '12 días',
                                  style: TextStyle(color: AppColors.wine, fontSize: 26, fontWeight: FontWeight.w900),
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  children: const [
                                    Icon(Icons.bolt, color: AppColors.darkGreen, size: 15),
                                    SizedBox(width: 4),
                                    Text(
                                      '¡Imbatible! Sigue hoy',
                                      style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold),
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
                              borderRadius: BorderRadius.circular(24),
                              border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Meta Mes',
                                  style: TextStyle(color: AppColors.wine, fontSize: 12.5, fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  crossAxisAlignment: CrossAxisAlignment.baseline,
                                  textBaseline: TextBaseline.alphabetic,
                                  children: const [
                                    Text(
                                      '48',
                                      style: TextStyle(color: AppColors.wine, fontSize: 26, fontWeight: FontWeight.w900),
                                    ),
                                    Text(
                                      ' / 100 pts',
                                      style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(6),
                                  child: const LinearProgressIndicator(
                                    value: 0.48,
                                    backgroundColor: AppColors.cream,
                                    color: AppColors.darkGreen,
                                    minHeight: 8,
                                  ),
                                ),
                                const SizedBox(height: 10),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: const [
                                    Text('Semana 2 activa', style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
                                    Text('48%', style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // Diagnóstico de 4 Semanas
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
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
                                style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 14),
                              ),
                              const Spacer(),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                decoration: BoxDecoration(
                                  color: AppColors.lime,
                                  borderRadius: BorderRadius.circular(14),
                                ),
                                child: const Text(
                                  'Mes 1 • Hábitos',
                                  style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 14),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceAround,
                            children: ['L', 'M', 'M', 'J', 'V', 'S', 'D', 'Meta'].map((d) {
                              return Text(
                                d,
                                style: TextStyle(
                                  color: d == 'Meta' ? AppColors.wine : AppColors.darkGreen,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 11.5,
                                ),
                              );
                            }).toList(),
                          ),
                          const SizedBox(height: 12),
                          _buildCompletedWeekCard(
                            title: 'Semana 1 • Hábito Inicial',
                            subtitle: 'Registro diario consolidado',
                            badgeText: '25/25 pts',
                            days: ['1', '2', '3', '4', '5', '6', '7'],
                          ),
                          const SizedBox(height: 12),
                          _buildActiveWeekCard(
                            title: 'Semana 2 • En Juego (Actual)',
                            subtitle: 'Categorizando gastos hormiga',
                            badgeText: '23/25 pts',
                            days: ['8', '9', '10', '11', '12', '13', '14'],
                          ),
                          const SizedBox(height: 12),
                          _buildLockedWithTimerCard(
                            title: 'Semana 3 • Consistencia',
                            subtitle: 'Detección de patrones',
                            timerText: 'Inicia en 2 días',
                            days: ['15', '16', '17', '18', '19', '20', '21'],
                          ),
                          const SizedBox(height: 12),
                          _buildGraduationWeekCard(
                            title: 'Semana 4 • Graduación Etapa 1',
                            subtitle: 'Piloto Automático desbloqueable',
                            badgeText: 'Cofre Épico',
                            days: ['22', '23', '24', '25', '26', '27', '28'],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Cuadro de motivación Nancy
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 38,
                            height: 38,
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
                                  style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12.5),
                                ),
                                SizedBox(height: 3),
                                Text(
                                  '¡Vas volando! Estás a solo 2 días de superar la mitad del diagnóstico. Al culminar la Semana 4 desbloquearás el Piloto Automático de Ahorro.',
                                  style: TextStyle(color: AppColors.darkGreen, fontSize: 11.5, height: 1.3),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    // ===================================================
                    // BOTÓN INFERIOR "MANTÉN PARA HABLAR"
                    // ===================================================
                    GestureDetector(
                      onTap: () {
                        showModalBottomSheet(
                          context: context,
                          isScrollControlled: true,
                          backgroundColor: Colors.transparent,
                          builder: (context) => VoiceRecordingModal(
                            accessToken: "TU_TOKEN_DE_ACCESO_AQUI",
                            onSuccess: (responseData) {
                              print("¡Gasto procesado con éxito!: $responseData");
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text("¡Audio enviado y registrado correctamente!")),
                              );
                            },
                            onManualRegister: () {
                              Navigator.pop(context); // Cierra voz
                              showModalBottomSheet(
                                context: context,
                                isScrollControlled: true,
                                backgroundColor: Colors.transparent,
                                builder: (context) => ManualRegisterModal(
                                  onBackToVoice: () {
                                    Navigator.pop(context); // Cierra manual
                                  },
                                ),
                              );
                            },
                          ),
                        );
                      },
                      child: Container(
                        height: 52,
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                          color: AppColors.lime,
                          borderRadius: BorderRadius.circular(26),
                          border: const Border(
                            bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
                          ),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
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
                            Column(
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
                          ],
                        ),
                      ),
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

  Widget _buildCompletedWeekCard({required String title, required String subtitle, required String badgeText, required List<String> days}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withOpacity(0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 22,
                height: 22,
                decoration: const BoxDecoration(color: AppColors.darkGreen, shape: BoxShape.circle),
                child: const Icon(Icons.check, color: AppColors.cream, size: 13),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12)),
                  Text(subtitle, style: const TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                ],
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: AppColors.lime, borderRadius: BorderRadius.circular(14)),
                child: Text(badgeText, style: const TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: days.map((d) => Column(
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: const BoxDecoration(color: AppColors.darkGreen, shape: BoxShape.circle),
                  child: const Center(child: Icon(Icons.check, color: AppColors.cream, size: 14)),
                ),
                const SizedBox(height: 4),
                Text(d, style: const TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
              ],
            )).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildActiveWeekCard({required String title, required String subtitle, required String badgeText, required List<String> days}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.mutedPink.withOpacity(0.2),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 22,
                height: 22,
                decoration: const BoxDecoration(color: AppColors.wine, shape: BoxShape.circle),
                child: const Icon(Icons.play_arrow, color: AppColors.cream, size: 13),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12)),
                  Text(subtitle, style: const TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                ],
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: AppColors.mutedPink, borderRadius: BorderRadius.circular(14)),
                child: Text(badgeText, style: const TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: days.map((d) {
              final isStarDay = d == '13';
              final isPinkDay = d == '14';
              if (isStarDay) {
                return Column(
                  children: [
                    Container(
                      width: 24,
                      height: 24,
                      decoration: BoxDecoration(color: Colors.amber.shade300, shape: BoxShape.circle),
                      child: const Center(child: Icon(Icons.star, color: AppColors.wine, size: 14)),
                    ),
                    const SizedBox(height: 4),
                    Text(d, style: const TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold)),
                  ],
                );
              }
              if (isPinkDay) {
                return Column(
                  children: [
                    Container(
                      width: 24,
                      height: 24,
                      decoration: const BoxDecoration(color: AppColors.mutedPink, shape: BoxShape.circle),
                      child: Center(child: Text(d, style: const TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold))),
                    ),
                    const SizedBox(height: 4),
                    Text(d, style: const TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold)),
                  ],
                );
              }
              return Column(
                children: [
                  Container(
                    width: 24,
                    height: 24,
                    decoration: const BoxDecoration(color: AppColors.darkGreen, shape: BoxShape.circle),
                    child: const Center(child: Icon(Icons.check, color: AppColors.cream, size: 14)),
                  ),
                  const SizedBox(height: 4),
                  Text(d, style: const TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildLockedWithTimerCard({required String title, required String subtitle, required String timerText, required List<String> days}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cream.withOpacity(0.6),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withOpacity(0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.lock_outline, color: AppColors.wine, size: 18),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: TextStyle(color: AppColors.wine.withOpacity(0.7), fontWeight: FontWeight.bold, fontSize: 12)),
                  Text(subtitle, style: TextStyle(color: AppColors.darkGreen.withOpacity(0.7), fontSize: 10)),
                ],
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: AppColors.cardCream, borderRadius: BorderRadius.circular(14)),
                child: Text(timerText, style: TextStyle(color: AppColors.darkGreen.withOpacity(0.8), fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: days.map((d) => Column(
              children: [
                Icon(Icons.lock_outline, color: AppColors.wine.withOpacity(0.3), size: 18),
                const SizedBox(height: 6),
                Text(d, style: TextStyle(color: AppColors.wine.withOpacity(0.4), fontSize: 11, fontWeight: FontWeight.bold)),
              ],
            )).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildGraduationWeekCard({required String title, required String subtitle, required String badgeText, required List<String> days}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cream.withOpacity(0.6),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withOpacity(0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.lock_outline, color: AppColors.wine, size: 18),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: TextStyle(color: AppColors.wine.withOpacity(0.7), fontWeight: FontWeight.bold, fontSize: 12)),
                  Text(subtitle, style: TextStyle(color: AppColors.darkGreen.withOpacity(0.7), fontSize: 10)),
                ],
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: AppColors.mutedPink.withOpacity(0.6), borderRadius: BorderRadius.circular(14)),
                child: Row(
                  children: [
                    const Icon(Icons.card_giftcard, color: AppColors.wine, size: 12),
                    const SizedBox(width: 4),
                    Text(badgeText, style: const TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: days.map((d) {
              final isLastDay = d == '28';
              if (isLastDay) {
                return Column(
                  children: [
                    const Icon(Icons.card_giftcard, color: AppColors.wine, size: 18),
                    const SizedBox(height: 6),
                    Text(d, style: TextStyle(color: AppColors.wine.withOpacity(0.7), fontSize: 11, fontWeight: FontWeight.bold)),
                  ],
                );
              }
              return Column(
                children: [
                  Icon(Icons.lock_outline, color: AppColors.wine.withOpacity(0.3), size: 18),
                  const SizedBox(height: 6),
                  Text(d, style: TextStyle(color: AppColors.wine.withOpacity(0.4), fontSize: 11, fontWeight: FontWeight.bold)),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}