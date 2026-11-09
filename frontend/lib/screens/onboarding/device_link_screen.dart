import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../services/api_service.dart';
import '../../services/auth_session.dart';
import '../../theme/app_colors.dart';
import 'stages_overview_screen.dart';

enum LinkState { linking, qrScanner, success, connectionLost, error }

class DeviceLinkScreen extends StatefulWidget {
const DeviceLinkScreen({super.key});

@override
State<DeviceLinkScreen> createState() => _DeviceLinkScreenState();
}

class _DeviceLinkScreenState extends State<DeviceLinkScreen> {
LinkState currentState = LinkState.linking;
final TextEditingController _pinController = TextEditingController();
bool _isPairing = false;
String? _pairError;
String? _deviceToken;
static const String _deviceUid = 'FINAGOTCHI-PC-SIMULATOR-01';

@override
void dispose() {
_pinController.dispose();
super.dispose();
}

Future<void> _connectWithPin() async {
if (_isPairing) return;
final pin = _pinController.text.trim();
if (!RegExp(r'^\d{6}$').hasMatch(pin)) {
setState(() => _pairError = 'Introduce los 6 números del PIN de Nancy.');
return;
}
final token = AuthSession.accessToken;
if (token == null || token.isEmpty) {
setState(() => _pairError = 'Inicia sesión para vincular a Nancy.');
return;
}
setState(() {
_isPairing = true;
_pairError = null;
});
try {
final response = await ApiService().pairDevice(
accessToken: token,
deviceUid: _deviceUid,
pin: pin,
);
final data = response['data'] is Map
? Map<String, dynamic>.from(response['data'] as Map)
    : response;
final deviceToken = data['device_token']?.toString();
if (deviceToken == null || deviceToken.isEmpty) {
throw StateError('El servidor no devolvió el token del dispositivo.');
}
if (!mounted) return;
setState(() {
_deviceToken = deviceToken;
currentState = LinkState.success;
});
} catch (error) {
if (!mounted) return;
setState(() => _pairError = 'No se pudo vincular Nancy: $error');
} finally {
if (mounted) setState(() => _isPairing = false);
}
}

@override
Widget build(BuildContext context) {
return Scaffold(
backgroundColor: AppColors.cream,
appBar: AppBar(
backgroundColor: Colors.transparent,
elevation: 0,
title: Text(
_getAppBarTitle(),
style: const TextStyle(color: Colors.grey, fontSize: 12),
),
actions: [
PopupMenuButton<LinkState>(
icon: const Icon(Icons.bug_report, color: AppColors.wine),
onSelected: (state) => setState(() => currentState = state),
itemBuilder: (context) => [
const PopupMenuItem(
value: LinkState.linking,
child: Text('V03.1 Enlazar (QR o PIN)'),
),
const PopupMenuItem(
value: LinkState.qrScanner,
child: Text('V03.3 Escáner QR'),
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

String _getAppBarTitle() {
switch (currentState) {
case LinkState.linking:
return 'V03.1 Elegir método (QR o PIN)';
case LinkState.qrScanner:
return 'QR';
case LinkState.success:
return 'V03.4 Resultado (éxito)';
case LinkState.connectionLost:
return 'V03.4 Resultado (conexion perdida)';
case LinkState.error:
return 'V03.4 Resultado (error)';
}
}

Widget _buildStateView() {
switch (currentState) {
case LinkState.linking:
return _LinkingView(
onCancel: () => Navigator.pop(context),
onOpenScanner: () => setState(() => currentState = LinkState.qrScanner),
pinController: _pinController,
isPairing: _isPairing,
errorMessage: _pairError,
onConnect: _connectWithPin,
);
case LinkState.qrScanner:
return _QrScannerView(
onBackToManual: () => setState(() => currentState = LinkState.linking),
);
case LinkState.success:
return _SuccessView(deviceToken: _deviceToken);
case LinkState.connectionLost:
return _ConnectionLostView(
onReconnect: () => setState(() => currentState = LinkState.linking),
);
case LinkState.error:
return _ErrorView(
onRetry: () => setState(() => currentState = LinkState.linking),
onChangeMethod: () => setState(() => currentState = LinkState.linking),
);
}
}
}

// =====================================================================
// 1. V03.1 ELEGIR MÉTODO (QR O PIN)
// =====================================================================
class _LinkingView extends StatelessWidget {
final TextEditingController pinController;
final bool isPairing;
final String? errorMessage;
final VoidCallback onCancel;
final VoidCallback onOpenScanner;
final VoidCallback onConnect;

const _LinkingView({
required this.pinController,
required this.isPairing,
required this.errorMessage,
required this.onCancel,
required this.onOpenScanner,
required this.onConnect,
});

@override
Widget build(BuildContext context) {
return SingleChildScrollView(
key: const ValueKey('linking'),
padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
child: Column(
crossAxisAlignment: CrossAxisAlignment.center,
children: [
SizedBox(
height: 130,
child: Image.asset(
'assets/animations/nancy_walk_512.gif',
fit: BoxFit.contain,
),
),
const SizedBox(height: 8),
const Text(
'Enlaza tu finagotchi',
style: TextStyle(
fontSize: 22,
fontWeight: FontWeight.w900,
color: AppColors.wine,
height: 1.1,
),
),
const SizedBox(height: 4),
const Text(
'Elige cómo prefieres conectar tu dispositivo\nFinagotchi a tu teléfono.',
textAlign: TextAlign.center,
style: TextStyle(color: AppColors.darkGreen, fontSize: 12, height: 1.35),
),
const SizedBox(height: 18),
Container(
padding: const EdgeInsets.all(16),
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(20),
border: Border.all(color: AppColors.darkGreen.withOpacity(0.2), width: 1.5),
),
child: Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: [
Row(
children: [
Container(
padding: const EdgeInsets.all(8),
decoration: BoxDecoration(
color: AppColors.wine,
borderRadius: BorderRadius.circular(12),
),
child: const Icon(Icons.qr_code_scanner, color: AppColors.cardCream, size: 20),
),
const SizedBox(width: 10),
Container(
padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
decoration: BoxDecoration(
color: AppColors.mutedPink,
borderRadius: BorderRadius.circular(8),
),
child: const Text(
'RECOMENDADO',
style: TextStyle(
fontSize: 9,
fontWeight: FontWeight.w900,
color: AppColors.wine,
),
),
),
const Spacer(),
const Icon(Icons.arrow_circle_right_outlined, color: AppColors.darkGreen, size: 26),
],
),
const SizedBox(height: 8),
const Text(
'Escanear código QR',
style: TextStyle(
fontSize: 14,
fontWeight: FontWeight.bold,
color: AppColors.wine,
),
),
const SizedBox(height: 2),
const Text(
'Apunta la cámara al código QR que aparece en la\npantallita de tu Finagotchi.',
style: TextStyle(fontSize: 11.5, color: AppColors.darkGreen, height: 1.3),
),
const SizedBox(height: 14),
SizedBox(
width: double.infinity,
height: 40,
child: ElevatedButton.icon(
onPressed: onOpenScanner,
icon: const Icon(Icons.camera_alt_outlined, size: 16),
label: const Text('Abrir Escáner de Cámara', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
style: ElevatedButton.styleFrom(
backgroundColor: AppColors.darkGreen,
foregroundColor: AppColors.cardCream,
elevation: 0,
shape: const StadiumBorder(),
),
),
),
],
),
),
const SizedBox(height: 14),
Row(
children: const [
Expanded(child: Divider(thickness: 1, color: Color(0xFFE8D5C0))),
Padding(
padding: EdgeInsets.symmetric(horizontal: 10),
child: Text(
'O INGRESA CLAVE MANUAL',
style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppColors.wine),
),
),
Expanded(child: Divider(thickness: 1, color: Color(0xFFE8D5C0))),
],
),
const SizedBox(height: 14),
Container(
padding: const EdgeInsets.all(16),
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(20),
border: Border.all(color: AppColors.wine.withOpacity(0.25), width: 1.5),
),
child: Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: [
Row(
children: [
Container(
padding: const EdgeInsets.all(8),
decoration: BoxDecoration(
color: AppColors.mutedPink,
borderRadius: BorderRadius.circular(12),
),
child: const Icon(Icons.pin, color: AppColors.wine, size: 20),
),
const SizedBox(width: 10),
Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: const [
Text(
'Código PIN o Clave',
style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.wine),
),
Text(
'Escribe los 6 dígitos mostrados en pantalla',
style: TextStyle(fontSize: 11, color: AppColors.darkGreen),
),
],
),
],
),
const SizedBox(height: 14),
TextField(
controller: pinController,
keyboardType: TextInputType.number,
textAlign: TextAlign.center,
maxLength: 6,
inputFormatters: [FilteringTextInputFormatter.digitsOnly],
style: const TextStyle(
color: AppColors.darkGreen,
fontSize: 24,
fontWeight: FontWeight.w900,
letterSpacing: 12,
),
decoration: InputDecoration(
hintText: '••••••',
counterText: '',
filled: true,
fillColor: AppColors.cream,
border: OutlineInputBorder(
borderRadius: BorderRadius.circular(12),
),
),
),
if (errorMessage != null)
Padding(
padding: const EdgeInsets.only(top: 8),
child: Text(errorMessage!,
style: const TextStyle(color: Colors.red, fontSize: 12)),
),
const SizedBox(height: 10),
Row(
mainAxisAlignment: MainAxisAlignment.spaceBetween,
children: [
const Text(
'Ejemplo: 729-408',
style: TextStyle(fontSize: 10, color: AppColors.darkGreen),
),
GestureDetector(
onTap: () => ScaffoldMessenger.of(context).showSnackBar(
const SnackBar(content: Text('El PIN aparece en la consola de Nancy al iniciar el simulador.')),
),
child: const Text(
'¿Dónde está mi PIN?',
style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.wine, decoration: TextDecoration.underline),
),
),
],
),
],
),
),
const SizedBox(height: 12),
Container(
padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
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
'Mantén el dispositivo encendido y cerca de tu celular. Esto toma sólo unos segundos.',
style: TextStyle(fontSize: 11, color: Color(0xFF005691), fontWeight: FontWeight.w500, height: 1.2),
),
),
],
),
),
const SizedBox(height: 16),
Container(
height: 48,
width: double.infinity,
decoration: BoxDecoration(
color: AppColors.lime,
borderRadius: BorderRadius.circular(24),
border: const Border(
bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
),
),
child: InkWell(
onTap: isPairing ? null : onConnect,
borderRadius: BorderRadius.circular(24),
child: Row(
mainAxisAlignment: MainAxisAlignment.center,
children: const [
Text(
'Conectar',
style: TextStyle(
color: AppColors.darkGreen,
fontWeight: FontWeight.w900,
fontSize: 15,
),
),
SizedBox(width: 6),
Icon(Icons.arrow_forward, color: AppColors.darkGreen, size: 18),
],
),
),
),
const SizedBox(height: 10),
TextButton(
onPressed: onCancel,
child: const Text(
'Cancelar proceso',
style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12.5, decoration: TextDecoration.underline),
),
),
],
),
);
}

Widget _buildPinBox(String character) {
return Container(
width: 40,
height: 46,
alignment: Alignment.center,
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(12),
border: Border.all(color: AppColors.darkGreen, width: 1.5),
),
child: Text(
character,
style: TextStyle(
fontSize: 16,
fontWeight: FontWeight.bold,
color: character == '•' ? AppColors.darkGreen.withOpacity(0.4) : AppColors.darkGreen,
),
),
);
}
}

// =====================================================================
// 2. V03.3 ESCÁNER DE CÁMARA (QR)
// =====================================================================
class _QrScannerView extends StatelessWidget {
final VoidCallback onBackToManual;

const _QrScannerView({required this.onBackToManual});

@override
Widget build(BuildContext context) {
return SingleChildScrollView(
key: const ValueKey('scanner'),
padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
child: Column(
children: [
Container(
height: 310,
width: double.infinity,
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(26),
border: Border.all(color: AppColors.darkGreen.withOpacity(0.2), width: 1.5),
),
child: Stack(
alignment: Alignment.center,
children: [
Container(
width: 145,
height: 185,
padding: const EdgeInsets.all(10),
decoration: BoxDecoration(
color: Colors.white,
borderRadius: BorderRadius.circular(16),
boxShadow: [
BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 10, offset: const Offset(0, 4)),
],
),
child: Column(
mainAxisAlignment: MainAxisAlignment.center,
children: [
const Text('• NANCY LCD', style: TextStyle(fontSize: 8.5, fontWeight: FontWeight.w900, color: AppColors.wine)),
const SizedBox(height: 8),
const Icon(Icons.qr_code_2, size: 78, color: AppColors.wine),
const SizedBox(height: 6),
const Text('V03 • ID: FIN-8820', style: TextStyle(fontSize: 7.5, color: AppColors.darkGreen, fontWeight: FontWeight.w600)),
],
),
),
Positioned(top: 26, left: 26, child: _buildCorner(true, true)),
Positioned(top: 26, right: 26, child: _buildCorner(true, false)),
Positioned(bottom: 26, left: 26, child: _buildCorner(false, true)),
Positioned(bottom: 26, right: 26, child: _buildCorner(false, false)),
Positioned(
bottom: 16,
child: Container(
padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(16),
border: Border.all(color: AppColors.darkGreen.withOpacity(0.2)),
),
child: Row(
mainAxisSize: MainAxisSize.min,
children: const [
Icon(Icons.center_focus_strong, size: 14, color: AppColors.darkGreen),
SizedBox(width: 6),
Text(
'Centra el dispositivo en la retícula',
style: TextStyle(fontSize: 11, color: AppColors.darkGreen, fontWeight: FontWeight.bold),
),
],
),
),
),
],
),
),
const SizedBox(height: 12),
Container(
padding: const EdgeInsets.all(16),
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(20),
border: Border.all(color: AppColors.darkGreen.withOpacity(0.2), width: 1.5),
),
child: Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: [
Row(
children: [
const Text(
'Apunta al código QR',
style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: AppColors.wine),
),
const Spacer(),
Container(
padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
decoration: BoxDecoration(
color: AppColors.mutedPink,
borderRadius: BorderRadius.circular(10),
),
child: const Text(
'● Escaneando',
style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w900, color: AppColors.wine),
),
),
],
),
const SizedBox(height: 6),
const Text(
'Enfoca la pantallita de tu Finagotchi dentro del\nrecuadro para sincronizar sus finanzas y su energía.',
style: TextStyle(fontSize: 11.5, color: AppColors.darkGreen, height: 1.35),
),
const SizedBox(height: 12),
ClipRRect(
borderRadius: BorderRadius.circular(4),
child: LinearProgressIndicator(
value: 0.55,
backgroundColor: AppColors.mutedPink.withOpacity(0.6),
valueColor: const AlwaysStoppedAnimation<Color>(AppColors.darkGreen),
minHeight: 6,
),
),
const SizedBox(height: 14),
SizedBox(
width: double.infinity,
height: 48,
child: ElevatedButton(
onPressed: onBackToManual,
style: ElevatedButton.styleFrom(
backgroundColor: AppColors.darkGreen,
foregroundColor: AppColors.cardCream,
elevation: 0,
shape: const StadiumBorder(),
),
child: Row(
mainAxisAlignment: MainAxisAlignment.center,
children: const [
Icon(Icons.pin, size: 18, color: AppColors.cardCream),
SizedBox(width: 8),
Text(
'¿Prefieres ingresar el código PIN manual?',
style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12.5),
),
],
),
),
),
const SizedBox(height: 12),
Row(
mainAxisAlignment: MainAxisAlignment.spaceBetween,
children: [
GestureDetector(
onTap: () {},
child: const Text(
'¿Dónde está el QR?',
style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.bold, color: AppColors.wine, decoration: TextDecoration.underline),
),
),
GestureDetector(
onTap: () {},
child: const Text(
'Subir captura',
style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.bold, color: AppColors.wine, decoration: TextDecoration.underline),
),
),
],
),
],
),
),
const SizedBox(height: 10),
Container(
padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
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
'Mantén el dispositivo encendido y cerca de tu celular. Esto toma sólo unos segundos.',
style: TextStyle(fontSize: 11, color: Color(0xFF005691), fontWeight: FontWeight.w500, height: 1.2),
),
),
],
),
),
],
),
);
}

Widget _buildCorner(bool isTop, bool isLeft) {
return Container(
width: 28,
height: 28,
decoration: BoxDecoration(
border: Border(
top: isTop ? const BorderSide(color: AppColors.darkGreen, width: 4.0) : BorderSide.none,
bottom: !isTop ? const BorderSide(color: AppColors.darkGreen, width: 4.0) : BorderSide.none,
left: isLeft ? const BorderSide(color: AppColors.darkGreen, width: 4.0) : BorderSide.none,
right: !isLeft ? const BorderSide(color: AppColors.darkGreen, width: 4.0) : BorderSide.none,
),
),
);
}
}

// =====================================================================
// 3. V03.4 RESULTADO (ÉXITO)
// =====================================================================
class _SuccessView extends StatelessWidget {
final String? deviceToken;
const _SuccessView({this.deviceToken});

@override
Widget build(BuildContext context) {
return SingleChildScrollView(
padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
child: Column(
mainAxisAlignment: MainAxisAlignment.center,
children: [
SizedBox(
height: 150,
child: Image.asset(
'assets/images/nancy_corazones 1.png',
fit: BoxFit.contain,
),
),
const SizedBox(height: 12),
const Text(
'¡Listo, ya estamos\nenlazados!',
textAlign: TextAlign.center,
style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: AppColors.wine, height: 1.2),
),
const SizedBox(height: 6),
const Text(
'Tu FinaGotchi ya puede enviar tus\nregistros por voz a la app.',
textAlign: TextAlign.center,
style: TextStyle(color: AppColors.darkGreen, fontSize: 12.5, height: 1.3),
),
const SizedBox(height: 20),
Container(
padding: const EdgeInsets.all(16),
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(20),
border: Border.all(color: AppColors.darkGreen.withOpacity(0.2)),
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
const Divider(height: 20, thickness: 1),
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
const SizedBox(height: 12),
Container(
padding: const EdgeInsets.all(12),
decoration: BoxDecoration(
color: AppColors.mutedPink.withOpacity(0.3),
borderRadius: BorderRadius.circular(16),
border: Border.all(color: AppColors.wine.withOpacity(0.15)),
),
child: Row(
children: const [
Icon(Icons.info_outline, size: 16, color: AppColors.wine),
SizedBox(width: 8),
Expanded(
child: Text(
'Nota: El dispositivo físico muestra animación de confirmación sincronizada.',
style: TextStyle(fontSize: 11, color: AppColors.wine, height: 1.2),
),
),
],
),
),
if (deviceToken != null) ...[
const SizedBox(height: 16),
const Text(
'Token para autorizar el simulador en tu PC:',
textAlign: TextAlign.center,
style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold),
),
const SizedBox(height: 8),
SelectableText(deviceToken!,
style: const TextStyle(fontSize: 11, color: AppColors.darkGreen)),
const SizedBox(height: 8),
ElevatedButton.icon(
onPressed: () async {
await Clipboard.setData(ClipboardData(text: deviceToken!));
if (context.mounted) {
ScaffoldMessenger.of(context).showSnackBar(
const SnackBar(content: Text('Token copiado. Pégalo en la consola de Nancy.')),
);
}
},
icon: const Icon(Icons.copy),
label: const Text('Copiar token para Nancy'),
),
],
const SizedBox(height: 24),
Container(
height: 48,
width: double.infinity,
decoration: BoxDecoration(
color: AppColors.lime,
borderRadius: BorderRadius.circular(24),
border: const Border(
bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
),
),
child: InkWell(
onTap: () {
Navigator.pushReplacement(
context,
MaterialPageRoute(
builder: (_) => const StagesOverviewScreen(),
),
);
},
borderRadius: BorderRadius.circular(24),
child: Row(
mainAxisAlignment: MainAxisAlignment.center,
children: const [
Text('Continuar', style: TextStyle(fontWeight: FontWeight.w900, color: AppColors.darkGreen, fontSize: 15)),
SizedBox(width: 6),
Icon(Icons.arrow_forward, color: AppColors.darkGreen, size: 18),
],
),
),
),
],
),
);
}
}

// =====================================================================
// 4. V03.4 RESULTADO (CONEXIÓN PERDIDA) - CON logoAzul.png
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
const Icon(Icons.wifi_off, color: Color(0xFF004B75), size: 20),
const SizedBox(width: 10),
Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: const [
Text(
'Conexión perdida',
style: TextStyle(fontSize: 12, color: Color(0xFF004B75), fontWeight: FontWeight.bold),
),
Text(
'Buscando enlace cercano',
style: TextStyle(fontSize: 10.5, color: Color(0xFF004B75)),
),
],
),
const Spacer(),
Container(
padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
decoration: BoxDecoration(
color: AppColors.mutedPink,
borderRadius: BorderRadius.circular(12),
),
child: const Text('2 pendientes', style: TextStyle(fontSize: 10, color: AppColors.wine, fontWeight: FontWeight.w900)),
),
],
),
),
const SizedBox(height: 24),
const Text(
'Perdimos la\nseñal con tu',
textAlign: TextAlign.center,
style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: brandBlue, height: 1.15),
),
const SizedBox(height: 6),
Image.asset(
'assets/images/logoAzul.png',
height: 26,
fit: BoxFit.contain,
),
const SizedBox(height: 10),
const Text(
'No te preocupes, tus registros están\nguardados y se enviarán cuando volvamos a\nconectarnos.',
textAlign: TextAlign.center,
style: TextStyle(fontSize: 12, color: brandBlue, height: 1.3),
),
const SizedBox(height: 18),
Container(
padding: const EdgeInsets.all(16),
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(20),
border: const Border(
bottom: BorderSide(color: cardBlueBorder, width: 3),
),
),
child: Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: [
Row(
children: [
const Icon(Icons.directions_car_outlined, color: brandBlue, size: 20),
const SizedBox(width: 10),
Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: const [
Text('finagotchi', style: TextStyle(fontWeight: FontWeight.bold, color: brandBlue, fontSize: 13)),
Text('ID: RF-22 • Enlazado', style: TextStyle(fontSize: 10.5, color: Colors.black54)),
],
),
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
Text('Sin conexión', style: TextStyle(fontSize: 10.5, color: AppColors.darkGreen, fontWeight: FontWeight.bold)),
],
),
),
],
),
const Padding(
padding: EdgeInsets.symmetric(vertical: 10),
child: Divider(height: 1, thickness: 1, color: Color(0xFFE8D5C0)),
),
Row(
mainAxisAlignment: MainAxisAlignment.spaceBetween,
children: const [
Text('🕒 Última vez: hace 5 min', style: TextStyle(fontSize: 11, color: Color(0xFF555555))),
Text('🔋 Batería: 15%', style: TextStyle(fontSize: 11, color: Color(0xFF555555))),
],
),
const SizedBox(height: 10),
Container(
padding: const EdgeInsets.all(10),
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(12),
border: Border.all(color: cardBlueBorder.withOpacity(0.3)),
),
child: Row(
children: const [
Icon(Icons.battery_alert, size: 18, color: brandBlue),
SizedBox(width: 10),
Expanded(
child: Text(
'Batería baja detectada\nConéctalo al cargador para despertar a Nancy',
style: TextStyle(fontSize: 11, color: brandBlue, height: 1.2, fontWeight: FontWeight.w600),
),
),
],
),
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
borderRadius: BorderRadius.circular(20),
border: const Border(
bottom: BorderSide(color: cardBlueBorder, width: 3),
),
),
child: Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: [
const Text('¿Qué puede haber ocurrido?', style: TextStyle(fontWeight: FontWeight.bold, color: brandBlue, fontSize: 13)),
const SizedBox(height: 10),
_buildCauseRow(Icons.phone_android_outlined, 'Dispositivo apagado o sin batería suficiente', brandBlue),
const SizedBox(height: 8),
_buildCauseRow(Icons.location_on_outlined, 'Estás lejos del rango de alcance (más de 5 metros)', brandBlue),
const SizedBox(height: 8),
_buildCauseRow(Icons.bluetooth_disabled_outlined, 'Wi-Fi o Bluetooth desactivado en tu teléfono', brandBlue),
],
),
),
const SizedBox(height: 14),
const Text(
'● Reintentando automáticamente en 8s...',
style: TextStyle(fontSize: 11, color: brandBlue, fontWeight: FontWeight.bold),
),
const SizedBox(height: 16),
Container(
decoration: BoxDecoration(
borderRadius: BorderRadius.circular(30),
border: const Border(
bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
),
),
child: SizedBox(
width: double.infinity,
height: 48,
child: ElevatedButton.icon(
onPressed: onReconnect,
icon: const Icon(Icons.refresh, color: AppColors.darkGreen),
label: const Text('Reconectar ahora', style: TextStyle(fontWeight: FontWeight.w900, color: AppColors.darkGreen, fontSize: 14)),
style: ElevatedButton.styleFrom(backgroundColor: AppColors.lime, shape: const StadiumBorder(), elevation: 0),
),
),
),
const SizedBox(height: 4),
TextButton(
onPressed: () => Navigator.pop(context),
child: const Text('Más tarde', style: TextStyle(color: brandBlue, fontWeight: FontWeight.bold, fontSize: 12.5)),
),
],
),
);
}

Widget _buildCauseRow(IconData icon, String text, Color color) {
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
style: TextStyle(fontSize: 11, color: color, height: 1.2),
),
),
],
);
}
}

// =====================================================================
// 5. V03.4 RESULTADO (ERROR) - CON logoNaranja.png Y CAMBIO DE MÉTODO
// =====================================================================
class _ErrorView extends StatelessWidget {
final VoidCallback onRetry;
final VoidCallback onChangeMethod;

const _ErrorView({
required this.onRetry,
required this.onChangeMethod,
});

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
borderRadius: BorderRadius.circular(20),
border: const Border(
bottom: BorderSide(color: AppColors.orangeAlert, width: 3),
),
),
child: Row(
children: [
const Icon(Icons.info_outline, color: AppColors.orangeAlert, size: 20),
const SizedBox(width: 10),
const Expanded(
child: Text(
'El dispositivo no respondió a tiempo. Prueba verificando que esté encendido y con la pantalla activa.',
style: TextStyle(fontSize: 11.5, color: AppColors.orangeAlert, height: 1.25, fontWeight: FontWeight.w500),
),
),
],
),
),
const SizedBox(height: 24),
const Text(
'No pudimos\nenlazar tu',
textAlign: TextAlign.center,
style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: AppColors.orangeAlert, height: 1.15),
),
const SizedBox(height: 6),
Image.asset(
'assets/images/logoNaranja.png',
height: 26,
fit: BoxFit.contain,
),
const SizedBox(height: 10),
const Text(
'No te preocupes, tus registros están\nguardados y se enviarán cuando volvamos a\nconectarnos.',
textAlign: TextAlign.center,
style: TextStyle(fontSize: 12, color: AppColors.darkGreen, height: 1.3),
),
const SizedBox(height: 20),
Container(
width: double.infinity,
padding: const EdgeInsets.all(16),
decoration: BoxDecoration(
color: AppColors.cardCream,
borderRadius: BorderRadius.circular(20),
border: const Border(
bottom: BorderSide(color: AppColors.orangeAlert, width: 3),
),
),
child: Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: [
Row(
children: [
const Icon(Icons.build_outlined, size: 18, color: AppColors.orangeAlert),
const SizedBox(width: 8),
const Text('Cómo solucionarlo', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.orangeAlert, fontSize: 13)),
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
const SizedBox(height: 24),
Container(
decoration: BoxDecoration(
borderRadius: BorderRadius.circular(30),
border: const Border(
bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
),
),
child: SizedBox(
width: double.infinity,
height: 48,
child: ElevatedButton.icon(
onPressed: onRetry,
icon: const Icon(Icons.refresh, color: AppColors.darkGreen, size: 18),
label: const Text('Intentar de nuevo', style: TextStyle(fontWeight: FontWeight.w900, color: AppColors.darkGreen, fontSize: 14)),
style: ElevatedButton.styleFrom(backgroundColor: AppColors.lime, shape: const StadiumBorder(), elevation: 0),
),
),
),
const SizedBox(height: 10),
TextButton(
onPressed: onChangeMethod,
child: const Text(
'Cambiar método (QR o PIN)',
style: TextStyle(color: AppColors.darkGreen, fontSize: 12.5, fontWeight: FontWeight.bold, decoration: TextDecoration.underline),
),
),
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
const SizedBox(width: 10),
Expanded(child: Text(text, style: const TextStyle(fontSize: 11.5, color: AppColors.darkGreen, fontWeight: FontWeight.w500))),
],
);
}
}
