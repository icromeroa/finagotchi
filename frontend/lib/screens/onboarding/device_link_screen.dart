import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import 'stages_overview_screen.dart';

enum LinkState { linking, success, connectionLost, error }

class DeviceLinkScreen extends StatefulWidget {
  const DeviceLinkScreen({super.key});

  @override
  State<DeviceLinkScreen> createState() => _DeviceLinkScreenState();
}

class _DeviceLinkScreenState extends State<DeviceLinkScreen> {
  LinkState currentState = LinkState.linking;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          PopupMenuButton<LinkState>(
            icon: const Icon(Icons.bug_report, color: AppColors.wine),
            onSelected: (state) => setState(() => currentState = state),
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: LinkState.linking,
                child: Text('V03.1 Enlazando...'),
              ),
              const PopupMenuItem(
                value: LinkState.success,
                child: Text('V03.4 Éxito'),
              ),
              const PopupMenuItem(
                value: LinkState.connectionLost,
                child: Text('V03.4 Conexión perdida'),
              ),
              const PopupMenuItem(
                value: LinkState.error,
                child: Text('V03.4 Error de enlace'),
              ),
            ],
          ),
        ],
      ),
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          child: _buildStateView(),
        ),
      ),
    );
  }

  Widget _buildStateView() {
    switch (currentState) {
      case LinkState.linking:
        return _LinkingView(
          onCancel: () => Navigator.pop(context),
        );
      case LinkState.success:
        return const _SuccessView();
      case LinkState.connectionLost:
        return _ConnectionLostView(
          onReconnect: () => setState(() => currentState = LinkState.linking),
        );
      case LinkState.error:
        return _ErrorView(
          onRetry: () => setState(() => currentState = LinkState.linking),
        );
    }
  }
}

// =====================================================================
// 1. V03.1 ELEGIR MÉTODO / ENLAZANDO TU FINAGOTCHI
// =====================================================================
class _LinkingView extends StatelessWidget {
  final VoidCallback onCancel;

  const _LinkingView({required this.onCancel});

  @override
  Widget build(BuildContext context) {
    final softPinkBg = AppColors.mutedPink.withOpacity(0.25);

    return SingleChildScrollView(
      key: const ValueKey('linking'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            width: 160,
            height: 160,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: AppColors.mutedPink.withOpacity(0.5), width: 1.5),
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'Enlazando tu',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: AppColors.wine,
              height: 1.1,
            ),
          ),
          const SizedBox(height: 4),
          Image.asset(
            'assets/images/logo.png',
            height: 26,
            fit: BoxFit.contain,
            filterQuality: FilterQuality.none,
          ),
          const SizedBox(height: 10),
          const Text(
            'Mantén el dispositivo encendido y cerca\nde tu celular. Esto toma unos segundos.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.darkGreen, fontSize: 13, height: 1.35),
          ),
          const SizedBox(height: 22),
          Container(
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.darkGreen.withOpacity(0.15), width: 1.5),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                Column(
                  children: const [
                    Icon(Icons.phone_android, color: AppColors.wine, size: 22),
                    SizedBox(height: 4),
                    Text('Celular', style: TextStyle(fontSize: 10, color: AppColors.darkGreen, fontWeight: FontWeight.w600)),
                  ],
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(
                        10,
                            (index) => Container(
                          width: 4,
                          height: 1.5,
                          margin: const EdgeInsets.symmetric(horizontal: 2),
                          color: AppColors.wine.withOpacity(index == 5 ? 1.0 : 0.4),
                        ),
                      ),
                    ),
                  ),
                ),
                Column(
                  children: const [
                    Icon(Icons.directions_car_filled_outlined, color: AppColors.wine, size: 22),
                    SizedBox(height: 4),
                    Text('FinaGotchi', style: TextStyle(fontSize: 10, color: AppColors.darkGreen, fontWeight: FontWeight.w600)),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: softPinkBg,
              borderRadius: BorderRadius.circular(20),
              border: const Border(
                bottom: BorderSide(color: AppColors.darkGreen, width: 3),
              ),
            ),
            child: Column(
              children: [
                _buildStepRow(
                  icon: Icons.check_circle,
                  iconColor: AppColors.darkGreen,
                  title: 'Buscando dispositivo',
                  subtitle: 'Conexión inalámbrica detectada',
                  titleColor: AppColors.wine,
                  subtitleColor: AppColors.darkGreen,
                ),
                Divider(height: 24, thickness: 1, color: AppColors.wine.withOpacity(0.15)),
                _buildStepRow(
                  icon: Icons.sync,
                  iconColor: AppColors.wine,
                  title: 'Verificando código',
                  subtitle: 'Emparejando clave de seguridad...',
                  titleColor: AppColors.wine,
                  subtitleColor: AppColors.wine.withOpacity(0.7),
                ),
                Divider(height: 24, thickness: 1, color: AppColors.wine.withOpacity(0.15)),
                _buildStepRow(
                  icon: Icons.access_time,
                  iconColor: AppColors.wine.withOpacity(0.5),
                  title: 'Sincronizando datos',
                  subtitle: 'Cargando perfil de Nancy',
                  titleColor: AppColors.wine.withOpacity(0.7),
                  subtitleColor: AppColors.darkGreen,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            height: 6,
            decoration: BoxDecoration(
              color: softPinkBg,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Expanded(
                  flex: 45,
                  child: Container(
                    decoration: BoxDecoration(
                      color: AppColors.wine,
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                ),
                const Spacer(flex: 55),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.lightBlue,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF005691).withOpacity(0.3), width: 1),
            ),
            child: Row(
              children: const [
                Icon(Icons.info_outline, color: Color(0xFF005691), size: 18),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Está tardando un poco más de lo normal. Acércate al dispositivo.',
                    style: TextStyle(fontSize: 11, color: Color(0xFF005691), fontWeight: FontWeight.w500, height: 1.2),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          TextButton(
            onPressed: onCancel,
            child: const Text(
              'Cancelar',
              style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13, decoration: TextDecoration.underline),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStepRow({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required Color titleColor,
    required Color subtitleColor,
  }) {
    return Row(
      children: [
        Icon(icon, color: iconColor, size: 22),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: titleColor)),
              const SizedBox(height: 2),
              Text(subtitle, style: TextStyle(fontSize: 11, color: subtitleColor)),
            ],
          ),
        ),
      ],
    );
  }
}

// =====================================================================
// 2. V03.4 RESULTADO (ÉXITO) - Navega a StagesOverviewScreen
// =====================================================================
class _SuccessView extends StatelessWidget {
  const _SuccessView();

  @override
  Widget build(BuildContext context) {
    return Padding(
      key: const ValueKey('success'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Spacer(),
          const Text(
            '¡Listo, ya estamos\nenlazados!',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AppColors.wine, height: 1.2),
          ),
          const SizedBox(height: 10),
          const Text(
            'Tu FinaGotchi ya puede enviar tus\nregistros por voz a la app.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.darkGreen, fontSize: 13, height: 1.3),
          ),
          const SizedBox(height: 30),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(20),
              border: const Border(
                bottom: BorderSide(color: AppColors.darkGreen, width: 3),
              ),
            ),
            child: Column(
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink.withOpacity(0.4),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.smart_toy_outlined, color: AppColors.wine, size: 20),
                    ),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text('finagotchi', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.wine, fontSize: 13)),
                        Text('Pocket v2.4', style: TextStyle(fontSize: 11, color: Colors.black54)),
                      ],
                    ),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.lime,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text('● Conectado', style: TextStyle(fontSize: 10, color: AppColors.darkGreen, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
                const Divider(height: 24, thickness: 1),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text('📶 Wi-Fi sincronizado', style: TextStyle(fontSize: 11, color: AppColors.darkGreen)),
                    Text('🔋 Batería 85%', style: TextStyle(fontSize: 11, color: AppColors.darkGreen)),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.progressBackground,
              borderRadius: BorderRadius.circular(16),
              border: const Border(
                bottom: BorderSide(color: AppColors.darkGreen, width: 3),
              ),
            ),
            child: Row(
              children: const [
                Icon(Icons.info_outline, size: 16, color: AppColors.wine),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Nota: El dispositivo físico muestra animación de confirmación sincronizada.',
                    style: TextStyle(fontSize: 10, color: AppColors.wine, height: 1.2),
                  ),
                ),
              ],
            ),
          ),
          const Spacer(),
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(30),
              border: const Border(
                bottom: BorderSide(color: AppColors.darkGreen, width: 3),
              ),
            ),
            child: SizedBox(
              width: double.infinity,
              height: 46,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const StagesOverviewScreen(),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.lime,
                  foregroundColor: AppColors.darkGreen,
                  elevation: 0,
                  shape: const StadiumBorder(),
                ),
                child: const Text('Continuar →', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// =====================================================================
// 3. V03.4 RESULTADO (CONEXIÓN PERDIDA)
// =====================================================================
class _ConnectionLostView extends StatelessWidget {
  final VoidCallback onReconnect;

  const _ConnectionLostView({required this.onReconnect});

  @override
  Widget build(BuildContext context) {
    const Color brandBlue = Color(0xFF006B8D);
    const Color cardBlueBorder = Color(0xFF0083B0);

    return SingleChildScrollView(
      key: const ValueKey('lost'),
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: AppColors.lightBlue,
              borderRadius: BorderRadius.circular(20),
              border: const Border(
                bottom: BorderSide(color: cardBlueBorder, width: 3),
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.wifi_off, color: Color(0xFF004B75)),
                const SizedBox(width: 8),
                const Text(
                  'Conexión perdida\nBuscando enlace cercano',
                  style: TextStyle(fontSize: 11, color: Color(0xFF004B75), fontWeight: FontWeight.bold, height: 1.2),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Text('2 pendientes', style: TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'Perdimos la\nseñal con tu',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: brandBlue, height: 1.15),
          ),
          const SizedBox(height: 4),
          Image.asset(
            'assets/images/logoAzul.png',
            height: 26,
            fit: BoxFit.contain,
            filterQuality: FilterQuality.none,
          ),
          const SizedBox(height: 8),
          const Text(
            'No te preocupes, tus registros están\nguardados y se enviarán cuando volvamos a\nconectarnos.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 12, color: brandBlue, height: 1.3),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(16),
              border: const Border(
                bottom: BorderSide(color: cardBlueBorder, width: 3),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.directions_car_outlined, color: brandBlue),
                    const SizedBox(width: 8),
                    const Text('finagotchi', style: TextStyle(fontWeight: FontWeight.bold, color: brandBlue)),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF2E4D3),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Icon(Icons.error, size: 12, color: AppColors.darkGreen),
                          SizedBox(width: 4),
                          Text('Sin conexión', style: TextStyle(fontSize: 11, color: AppColors.darkGreen, fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text('🕒 Última vez: hace 5 min', style: TextStyle(fontSize: 11, color: Color(0xFF555555))),
                    Text('🔋 Batería: 15%', style: TextStyle(fontSize: 11, color: Color(0xFF555555))),
                  ],
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 10),
                  child: Divider(height: 1, thickness: 1, color: Color(0xFFE8D5C0)),
                ),
                Row(
                  children: const [
                    Icon(Icons.battery_alert, size: 16, color: brandBlue),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Batería baja detectada\nConéctalo al cargador para despertar a Nancy',
                        style: TextStyle(fontSize: 11, color: brandBlue, height: 1.2, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(16),
              border: const Border(
                bottom: BorderSide(color: cardBlueBorder, width: 3),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('¿Qué puede haber ocurrido?', style: TextStyle(fontWeight: FontWeight.bold, color: brandBlue, fontSize: 13)),
                const SizedBox(height: 10),
                _buildCauseRow(Icons.phone_android_outlined, 'Dispositivo apagado o sin batería suficiente'),
                const SizedBox(height: 8),
                _buildCauseRow(Icons.location_on_outlined, 'Estás lejos del rango de alcance (más de 5 metros)'),
                const SizedBox(height: 8),
                _buildCauseRow(Icons.bluetooth_disabled_outlined, 'Wi-Fi o Bluetooth desactivado en tu teléfono'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            '● Reintentando automáticamente en 8s...',
            style: TextStyle(fontSize: 11, color: brandBlue, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(30),
              border: const Border(
                bottom: BorderSide(color: AppColors.darkGreen, width: 3),
              ),
            ),
            child: SizedBox(
              width: double.infinity,
              height: 46,
              child: ElevatedButton.icon(
                onPressed: onReconnect,
                icon: const Icon(Icons.refresh, color: AppColors.darkGreen),
                label: const Text('Reconectar ahora', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.darkGreen)),
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.lime, shape: const StadiumBorder(), elevation: 0),
              ),
            ),
          ),
          const SizedBox(height: 4),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Más tarde', style: TextStyle(color: brandBlue, fontWeight: FontWeight.bold, fontSize: 12)),
          ),
        ],
      ),
    );
  }

  Widget _buildCauseRow(IconData icon, String text) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(6),
          decoration: const BoxDecoration(
            color: Color(0xFFF2E4D3),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, size: 14, color: AppColors.darkGreen),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(fontSize: 11, color: Color(0xFF006B8D), height: 1.2),
          ),
        ),
      ],
    );
  }
}

// =====================================================================
// 4. V03.4 RESULTADO (ERROR)
// =====================================================================
class _ErrorView extends StatelessWidget {
  final VoidCallback onRetry;

  const _ErrorView({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      key: const ValueKey('error'),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.orangeCard,
              borderRadius: BorderRadius.circular(16),
              border: const Border(
                bottom: BorderSide(color: AppColors.orangeAlert, width: 3),
              ),
            ),
            child: Row(
              children: const [
                Icon(Icons.info_outline, color: AppColors.orangeAlert, size: 18),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'El dispositivo no respondió a tiempo. Prueba verificando que esté encendido y con la pantalla activa.',
                    style: TextStyle(fontSize: 11, color: AppColors.orangeAlert, height: 1.25),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          const Text(
            'No pudimos\nenlazar tu',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppColors.orangeAlert, height: 1.15),
          ),
          const SizedBox(height: 6),
          Image.asset(
            'assets/images/logoNaranja.png',
            height: 26,
            fit: BoxFit.contain,
            filterQuality: FilterQuality.none,
          ),
          const SizedBox(height: 12),
          const Text(
            'No te preocupes, tus registros están\nguardados y se enviarán cuando volvamos a\nconectarnos.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 12, color: AppColors.darkGreen, height: 1.3),
          ),
          const SizedBox(height: 28),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardCream,
              borderRadius: BorderRadius.circular(16),
              border: const Border(
                bottom: BorderSide(color: AppColors.orangeAlert, width: 3),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    Icon(Icons.build_outlined, size: 18, color: AppColors.orangeAlert),
                    SizedBox(width: 8),
                    Text('Cómo solucionarlo', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.orangeAlert, fontSize: 13)),
                  ],
                ),
                const SizedBox(height: 12),
                _buildErrorStep('1', 'Enciende el dispositivo y revisa la batería.'),
                const SizedBox(height: 8),
                _buildErrorStep('2', 'Acércalo a tu celular.'),
                const SizedBox(height: 8),
                _buildErrorStep('3', 'Genera un nuevo QR o PIN en el dispositivo.'),
              ],
            ),
          ),
          const SizedBox(height: 48),
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(30),
              border: const Border(
                bottom: BorderSide(color: AppColors.darkGreen, width: 3),
              ),
            ),
            child: SizedBox(
              width: double.infinity,
              height: 46,
              child: ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh, color: AppColors.darkGreen, size: 18),
                label: const Text('Intentar de nuevo', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.darkGreen, fontSize: 13)),
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.lime, shape: const StadiumBorder(), elevation: 0),
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () {},
            child: const Text(
              'Cambiar método (QR o PIN)',
              style: TextStyle(color: AppColors.darkGreen, fontSize: 12, decoration: TextDecoration.underline),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildErrorStep(String num, String text) {
    return Row(
      children: [
        CircleAvatar(
          radius: 9,
          backgroundColor: AppColors.orangeAlert,
          child: Text(num, style: const TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold)),
        ),
        const SizedBox(width: 8),
        Expanded(child: Text(text, style: const TextStyle(fontSize: 11, color: AppColors.darkGreen))),
      ],
    );
  }
}