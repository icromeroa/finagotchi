
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

class ConsentScreen extends StatefulWidget {
  const ConsentScreen({super.key});

  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  bool accepted = false;

  final ScrollController _scrollController = ScrollController();
  final GlobalKey _termsKey = GlobalKey();
  final GlobalKey _privacyKey = GlobalKey();

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _goToSection(GlobalKey key) {
    final target = key.currentContext;
    if (target != null) {
      Scrollable.ensureVisible(
        target,
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeInOut,
        alignment: 0.02,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        backgroundColor: AppColors.cream,
        elevation: 0,
        scrolledUnderElevation: 0,
        toolbarHeight: 48,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.wine),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        controller: _scrollController,
        padding: const EdgeInsets.fromLTRB(19, 2, 19, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Etiqueta superior
            Center(
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 13,
                  vertical: 7,
                ),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(30),
                ),
                child: const Text(
                  '🐷 Transparencia de Nancy · Tus datos son tuyos',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 19),

            // Cabecera informativa
            Container(
              padding: const EdgeInsets.fromLTRB(15, 17, 15, 16),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(15),
                border: const Border(
                  bottom: BorderSide(
                    color: AppColors.darkGreen,
                    width: 3,
                  ),
                ),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'PASO PREVIO AL REGISTRO',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.3,
                    ),
                  ),
                  SizedBox(height: 7),
                  Text(
                    'Consentimiento informado y claro',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 16,
                      height: 1.2,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  SizedBox(height: 5),
                  Text(
                    'Queremos que confíes en cómo Nancy cuida de tu dinero y tu privacidad.',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 11.5,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 27),

            // Accesos a las secciones
            Row(
              children: [
                Expanded(
                  child: _sectionTab(
                    icon: Icons.gavel_rounded,
                    label: 'Términos',
                    selected: true,
                    onTap: () => _goToSection(_termsKey),
                  ),
                ),
                const SizedBox(width: 3),
                Expanded(
                  child: _sectionTab(
                    icon: Icons.verified_user_outlined,
                    label: 'Privacidad',
                    selected: false,
                    onTap: () => _goToSection(_privacyKey),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 31),

            // Tres puntos clave
            Container(
              padding: const EdgeInsets.fromLTRB(14, 14, 14, 13),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(18),
                border: const Border(
                  bottom: BorderSide(
                    color: AppColors.mutedPink,
                    width: 3,
                  ),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const CircleAvatar(
                        radius: 11,
                        backgroundColor: AppColors.mutedPink,
                        child: Icon(
                          Icons.lightbulb_outline,
                          color: AppColors.wine,
                          size: 14,
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Expanded(
                        child: Text(
                          'Lo que debes saber en 3 puntos',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _bullet(
                    '1',
                    'Seguridad blindada:',
                    ' Cifrado bancario en todas tus notas, categorías y transacciones por voz.',
                  ),
                  _bullet(
                    '2',
                    'Cero publicidad:',
                    ' No comercializamos ni transferimos tus datos a terceros ni agencias publicitarias.',
                  ),
                  _bullet(
                    '3',
                    'Control y libertad:',
                    ' Exporta tu información en CSV o borra tu cuenta y el historial de Nancy cuando quieras.',
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            // Términos y condiciones
            Container(
              key: _termsKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _sectionHeading(
                    Icons.menu_book_rounded,
                    '1. Términos y Condiciones de Uso',
                    AppColors.wine,
                  ),
                  const SizedBox(height: 8),

                  Container(
                    padding: const EdgeInsets.fromLTRB(13, 10, 13, 12),
                    decoration: BoxDecoration(
                      color: AppColors.cardCream,
                      borderRadius: BorderRadius.circular(16),
                      border: const Border(
                        bottom: BorderSide(
                          color: AppColors.mutedPink,
                          width: 3,
                        ),
                      ),
                    ),
                    child: Column(
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(
                              width: 24,
                              height: 23,
                              child: Checkbox(
                                value: accepted,
                                onChanged: (value) {
                                  setState(() {
                                    accepted = value ?? false;
                                  });
                                },
                                activeColor: AppColors.darkGreen,
                                checkColor: Colors.white,
                                side: const BorderSide(
                                  color: AppColors.wine,
                                  width: 1,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(3),
                                ),
                                materialTapTargetSize:
                                MaterialTapTargetSize.shrinkWrap,
                              ),
                            ),
                            const SizedBox(width: 5),
                            Expanded(
                              child: RichText(
                                text: const TextSpan(
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 10.5,
                                    height: 1.35,
                                  ),
                                  children: [
                                    TextSpan(text: 'He leído y acepto los '),
                                    TextSpan(
                                      text: 'Términos y la Política de Privacidad',
                                      style: TextStyle(
                                        color: AppColors.wine,
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    TextSpan(text: ' de FinaGotchi.'),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        SizedBox(
                          width: double.infinity,
                          height: 47,
                          child: ElevatedButton(
                            onPressed: accepted
                                ? () {
                              // Aquí se conectará el registro real.
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    'Aceptación registrada en esta pantalla.',
                                  ),
                                ),
                              );
                            }
                                : null,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.lime,
                              disabledBackgroundColor:
                              AppColors.progressBackground,
                              foregroundColor: AppColors.darkGreen,
                              disabledForegroundColor:
                              AppColors.darkGreen.withOpacity(0.5),
                              elevation: 2,
                              shadowColor:
                              AppColors.darkGreen.withOpacity(0.3),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(28),
                                side: const BorderSide(
                                  color: AppColors.darkGreen,
                                  width: 1.5,
                                ),
                              ),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                              ),
                            ),
                            child: const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Flexible(
                                  child: Text(
                                    'Aceptar y continuar con mi registro',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(
                                      fontSize: 11.5,
                                      fontWeight: FontWeight.w800,
                                    ),
                                  ),
                                ),
                                SizedBox(width: 6),
                                Icon(Icons.arrow_forward, size: 17),
                              ],
                            ),
                          ),
                        ),
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          style: TextButton.styleFrom(
                            foregroundColor: AppColors.wine,
                            padding: const EdgeInsets.symmetric(vertical: 5),
                            minimumSize: const Size(0, 30),
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          ),
                          child: const Text(
                            'Volver a crear cuenta',
                            style: TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 17),

                  _detailCard(
                    icon: Icons.lock_outline,
                    title: '2. Cuenta y Custodia de Credenciales',
                    text:
                    'Eres el único custodio de tus claves de acceso y de las sesiones biométricas en tu dispositivo móvil. FinaGotchi no te solicitará contraseñas ni códigos de autenticación mediante canales externos.',
                  ),

                  const SizedBox(height: 12),

                  _detailCard(
                    icon: Icons.savings_outlined,
                    title: '3. Monedas Virtuales y Salud de Nancy',
                    text:
                    'Las "monedas Fina", manzanas de nutrición y puntos de racha son elementos lúdicos internos para premiar tus hábitos de ahorro. En ningún caso representan divisas fiduciarias, saldos bancarios ni instrumentos de inversión financiera garantizada.',
                  ),

                  const SizedBox(height: 12),

                  _detailCard(
                    icon: Icons.smart_toy_outlined,
                    title: '4. Asistencia con IA y Comandos de Voz',
                    text:
                    'Los audios procesados para categorizar compras son interpretados localmente y mediante modelos de lenguaje protegidos. Los consejos ofrecidos por Nancy son de naturaleza formativa y no constituyen asesoría patrimonial regulada.',
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Política de privacidad
            Container(
              key: _privacyKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _sectionHeading(
                    Icons.shield_outlined,
                    '2. Política de Privacidad',
                    AppColors.darkGreen,
                  ),
                  const SizedBox(height: 12),

                  _detailCard(
                    icon: Icons.storage_outlined,
                    title: '1. Datos que Recopilamos',
                    text:
                    'Recopilamos nombre o apodo, correo electrónico, registro voluntario de ingresos y egresos, y fragmentos de voz únicamente mientras mantienes presionado el botón de micrófono para registrar un gasto.',
                  ),

                  const SizedBox(height: 12),

                  _detailCard(
                    icon: Icons.record_voice_over_outlined,
                    title: '2. Finalidad del Tratamiento',
                    text:
                    'Tus datos alimentan el estado de ánimo y los reportes de ahorro de Nancy. No compartimos tus hábitos de consumo con anunciantes ni intermediarios de perfiles comerciales.',
                  ),

                  const SizedBox(height: 12),

                  _detailCard(
                    icon: Icons.key_outlined,
                    title: '3. Cifrado y Almacenamiento',
                    text:
                    'Toda la información se cifra en tránsito mediante TLS 1.3 y en reposo mediante AES-256. Tus registros confidenciales solo son accesibles desde tus credenciales activas.',
                  ),

                  const SizedBox(height: 12),

                  _detailCard(
                    icon: Icons.person_outline,
                    title: '4. Derechos de Habeas Data',
                    text:
                    'Tienes el derecho irrestricto de acceder, corregir, actualizar o exigir la eliminación absoluta de tu cuenta y los datos acumulados por Nancy directamente desde la sección Ajustes.',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sectionTab({
    required IconData icon,
    required String label,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return SizedBox(
      height: 31,
      child: OutlinedButton.icon(
        onPressed: onTap,
        icon: Icon(icon, size: 13),
        label: Text(
          label,
          style: const TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w700,
          ),
        ),
        style: OutlinedButton.styleFrom(
          backgroundColor: selected ? AppColors.wine : AppColors.cream,
          foregroundColor:
          selected ? AppColors.cream : AppColors.darkGreen,
          side: BorderSide(
            color: selected ? AppColors.wine : AppColors.darkGreen,
            width: 1,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 8),
          shape: const StadiumBorder(),
        ),
      ),
    );
  }

  Widget _sectionHeading(
      IconData icon,
      String title,
      Color color,
      ) {
    return Row(
      children: [
        Container(
          width: 26,
          height: 26,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(7),
          ),
          child: Icon(
            icon,
            color: Colors.white,
            size: 17,
          ),
        ),
        const SizedBox(width: 7),
        Expanded(
          child: Text(
            title,
            style: TextStyle(
              color: color,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
      ],
    );
  }

  Widget _bullet(
      String number,
      String boldText,
      String description,
      ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 18,
            height: 18,
            decoration: const BoxDecoration(
              color: AppColors.darkGreen,
              shape: BoxShape.circle,
            ),
            alignment: Alignment.center,
            child: Text(
              number,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          const SizedBox(width: 9),
          Expanded(
            child: RichText(
              text: TextSpan(
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 10.5,
                  height: 1.35,
                ),
                children: [
                  TextSpan(
                    text: boldText,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  TextSpan(text: description),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _detailCard({
    required IconData icon,
    required String title,
    required String text,
  }) {
    return Container(
      padding: const EdgeInsets.fromLTRB(13, 13, 13, 14),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(14),
        border: const Border(
          bottom: BorderSide(
            color: AppColors.mutedPink,
            width: 3,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                icon,
                color: AppColors.wine,
                size: 14,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 7),
          Text(
            text,
            style: const TextStyle(
              color: AppColors.darkGreen,
              fontSize: 10.5,
              height: 1.6,
            ),
          ),
        ],
      ),
    );
  }
}
