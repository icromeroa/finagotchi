import 'package:flutter/material.dart';
import '../api/api_client.dart';
import '../api/grabador.dart';
import '../api/servicios.dart';
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
  int ingresos = 0;
  int ahorro = 0;
  int puntos = 0;
  String animo = 'FELIZ';
  int salud = 100;
  bool isRecording = false;
  bool cargando = true;
  String? errorConexion;

  final GrabadorVoz _grabador = GrabadorVoz();

  @override
  void initState() {
    super.initState();
    _cargarHome();
  }

  @override
  void dispose() {
    _grabador.dispose();
    super.dispose();
  }

  Future<void> _cargarHome() async {
    try {
      final datos = await api.home();
      if (!mounted) return;
      final hoy = (datos['hoy'] ?? {}) as Map<String, dynamic>;
      final mascota = (datos['mascota'] ?? {}) as Map<String, dynamic>;
      setState(() {
        dailyBudget = (hoy['presupuesto_diario'] ?? 0).toInt();
        spent = (hoy['gastos'] ?? 0).toInt();
        ingresos = (hoy['ingresos'] ?? 0).toInt();
        ahorro = (hoy['ahorro'] ?? 0).toInt();
        puntos = (datos['puntos'] ?? 0).toInt();
        animo = (mascota['animo'] ?? 'FELIZ').toString();
        salud = (mascota['salud'] ?? 100).toInt();
        cargando = false;
        errorConexion = null;
      });
    } on ApiError catch (e) {
      if (!mounted) return;
      setState(() {
        cargando = false;
        errorConexion = e.mensaje;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        cargando = false;
        errorConexion = 'No se pudo cargar la informaciÃ³n: $e';
      });
    }
  }

  /// Graba la voz y la manda al backend, que la transcribe e interpreta.
  Future<void> _hablar() async {
    if (!_grabador.puedeGrabar) {
      _message(
        'La voz no estÃ¡ disponible en web. Escribe tu frase con el botÃ³n de al lado.',
      );
      return;
    }
    try {
      await _grabador.iniciar();
      setState(() => isRecording = true);
    } catch (e) {
      _message('No se pudo empezar a grabar: $e');
    }
  }

  Future<void> _enviarAudio() async {
    try {
      final wav = await _grabador.detener();
      setState(() => isRecording = false);
      if (wav.isEmpty) return;

      _message('Entendiendo tu mensaje...');
      final mensaje = await api.enviarAudio(
        wav,
        messageId: 'app-${DateTime.now().millisecondsSinceEpoch}',
        duracion: duracionWav(wav),
      );
      await _mostrarPropuesta(mensaje);
      await _cargarHome();
    } on ApiError catch (e) {
      if (mounted) _message(e.mensaje);
    } catch (e) {
      if (mounted) _message('No se pudo enviar el audio: $e');
    }
  }

  Future<void> _mostrarPropuesta(Map<String, dynamic> mensaje) async {
    if (!mounted) return;
    final transacciones = (mensaje['transacciones'] ?? []) as List<dynamic>;
    final texto = (mensaje['texto_transcrito'] ?? '').toString();

    if (transacciones.isEmpty) {
      _message(texto.isEmpty ? 'No entendÃ­ tu mensaje.' : 'EntendÃ­: "$texto"');
      return;
    }

    final detalle = transacciones.map((t) {
      final item = t as Map<String, dynamic>;
      final monto = (item['monto'] ?? 0).toInt();
      final categoria = (item['categoria'] ?? 'Sin categorÃ­a').toString();
      final cuenta = (item['cuenta'] ?? '').toString();
      return '${item['tipo']} de $monto Â· $categoria'
          '${cuenta.isEmpty ? '' : ' Â· $cuenta'}';
    }).join('\n');

    final confirmar = await showDialog<bool>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: const Text('Â¿Registro esto?'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              if (texto.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text('"$texto"',
                      style: const TextStyle(fontStyle: FontStyle.italic)),
                ),
              Text(detalle),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(contexto, false),
            child: const Text('Descartar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(contexto, true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );

    if (confirmar != true || !mounted) return;
    try {
      final id = (mensaje['id'] ?? 0).toInt();
      await api.confirmarMensaje(id);
      _message('Registro guardado.');
    } on ApiError catch (e) {
      if (mounted) _message(e.mensaje);
    }
  }

  void _message(String texto) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(texto)));
  }

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
                                'â— Registra hoy para mantenerla',
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
                          onPressed: () => _message('AquÃ­ aparecerÃ¡n tus notificaciones.'),
                          icon: const Icon(
                            Icons.notifications_none,
                            color: AppColors.darkGreen,
                            size: 26,
                          ),
                        ),
                        IconButton(
                          onPressed: () => _message('Tu perfil estarÃ¡ disponible aquÃ­.'),
                          icon: const Icon(
                            Icons.account_circle_outlined,
                            color: AppColors.darkGreen,
                            size: 26,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 12),

                    // 2. GLOBO DE DIÃLOGO DE NANCY
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppColors.cardCream,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(color: AppColors.wine, width: 1.5),
                        ),
                        child: const Text(
                          'Â¿QuÃ© tal si me cuentas tu primer gasto?',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),

                    // 3. HABITACIÃ“N CLÃSICA DE FINAGOTCHI
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
                                'No se pudo cargar la habitaciÃ³n.',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: AppColors.wine),
                              ),
                            );
                          },
                        ),
                      ),
                    ),

                    // ESPACIO AMPLIADO (Aprox 1 cm de respiro para que no quede apiÃ±ado)
                    const SizedBox(height: 24),

                    // 4. BOTÃ“N FLOTANTE "Finaliza tu dÃ­a"
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
                              'Finaliza tu dÃ­a',
                              style: TextStyle(
                                color: AppColors.wine,
                                fontWeight: FontWeight.w800,
                                fontSize: 13.5,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'â€œAlmuerzo corriente 14 milâ€',
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

                    // 5. BOTONES DE ACCIÃ“N (MantÃ©n para hablar + Escribir)
                    Row(
                      children: [
                        Expanded(
                          flex: 65,
                          child: GestureDetector(
                            onLongPressStart: (_) => _hablar(),
                            onLongPressEnd: (_) => _enviarAudio(),
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
                                          'MantÃ©n para hablar',
                                          style: TextStyle(
                                            color: AppColors.darkGreen,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 12,
                                          ),
                                        ),
                                        Text(
                                          'â€œAlmuerzo corriente 14 milâ€',
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
                                    'Tope mÃ¡ximo',
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

                    // 7. TARJETA DE DIAGNÃ“STICO (Etapa 1 de 3)
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
                                'DiagnÃ³stico',
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
                                  'DÃ­a 1 de 30',
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
                              Text('0 puntos â˜…', style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),

                    // 8. ÃšLTIMOS MOVIMIENTOS
                    const Text(
                      'Ãšltimos movimientos',
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
                            'AÃºn no hay registros',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(height: 2),
                          const Text(
                            'MantÃ©n presionado el botÃ³n y cuÃ©ntame tu primer gasto.',
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
                              'âš¡ Demora menos de 3 segundos',
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

            // 9. NAVEGACIÃ“N INFERIOR
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
                          _navItem(Icons.bar_chart, 'MÃ©tricas', 1),
                          _navItem(Icons.manage_search, 'Historial', 2),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  // BÃ“VEDA DE AHORROS
                  InkWell(
                    onTap: () => _message('AquÃ­ estarÃ¡ tu bÃ³veda de ahorros.'),
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

  // ELEMENTOS DE NAVEGACIÃ“N
  Widget _navItem(IconData icon, String label, int index) {
    final active = selectedTab == index;

    return InkWell(
      onTap: () {
        setState(() => selectedTab = index);
        if (index != 0) {
          _message('$label estarÃ¡ disponible prÃ³ximamente.');
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

  // MENSAJES TEMPORALES: se usa el _message de la parte superior, que
  // revisa que la pantalla siga montada antes de mostrar el aviso.
}