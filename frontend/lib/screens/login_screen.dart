
import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../services/api_service.dart';
import '../services/auth_session.dart';
import 'register_screen.dart';
import 'onboarding/device_link_screen.dart';

class LoginScreen extends StatefulWidget {
const LoginScreen({super.key});

@override
State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
final emailController = TextEditingController();
final passwordController = TextEditingController();

final ApiService apiService = ApiService();

bool showPassword = false;
bool showErrors = false;
bool isLoading = false;

bool get emailIsValid =>
RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    .hasMatch(emailController.text.trim());

@override
void dispose() {
emailController.dispose();
passwordController.dispose();
super.dispose();
}

Future<void> login() async {
if (isLoading) return;

setState(() {
showErrors = true;
});

if (!emailIsValid || passwordController.text.isEmpty) {
return;
}

setState(() {
isLoading = true;
});

try {
final result = await apiService.login(
correo: emailController.text.trim(),
password: passwordController.text,
);

final data = Map<String, dynamic>.from(result['data']);
final tokens = Map<String, dynamic>.from(data['tokens']);
final usuario = Map<String, dynamic>.from(data['usuario']);

final accessToken = tokens['access_token'] as String;
final refreshToken = tokens['refresh_token'] as String;

AuthSession.start(
newAccessToken: accessToken,
newRefreshToken: refreshToken,
userData: usuario,
);

if (!mounted) return;

// REDIRECCIÓN A LA VINCULACIÓN DE NANCY
Navigator.pushReplacement(
context,
MaterialPageRoute(
builder: (_) => const DeviceLinkScreen(),
),
);
} catch (e) {
if (!mounted) return;

_message(
e.toString().replaceFirst('Exception: ', ''),
);
} finally {
if (mounted) {
setState(() {
isLoading = false;
});
}
}
}

void _message(String message) {
ScaffoldMessenger.of(context).showSnackBar(
SnackBar(content: Text(message)),
);
}

void recoverPassword() {
showModalBottomSheet(
context: context,
isScrollControlled: true,
backgroundColor: Colors.transparent,
builder: (_) => _RecoveryPanel(
onSend: (email) {
Navigator.pop(context);
_message(
RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    .hasMatch(email.trim())
? 'La recuperación aún no está conectada al backend.'
    : 'Escribe un correo válido.',
);
},
),
);
}

@override
Widget build(BuildContext context) {
return Scaffold(
backgroundColor: AppColors.wine,
body: SafeArea(
bottom: false,
child: LayoutBuilder(
builder: (context, constraints) {
return SingleChildScrollView(
child: ConstrainedBox(
constraints: BoxConstraints(
minHeight: constraints.maxHeight,
),
child: Column(
children: [
// Cabecera rosa con la imagen original.
SizedBox(
height: 210,
width: double.infinity,
child: ColoredBox(
color: AppColors.mutedPink,
child: Center(
child: Image.asset(
'assets/images/ojos_mejillas_nariz.png',
width: double.infinity,
height: 155,
fit: BoxFit.contain,
filterQuality: FilterQuality.none,
),
),
),
),

// Panel vino con borde lima.
Container(
width: double.infinity,
constraints:
const BoxConstraints(minHeight: 475),
padding:
const EdgeInsets.fromLTRB(20, 40, 20, 30),
decoration: const BoxDecoration(
color: AppColors.wine,
borderRadius: BorderRadius.vertical(
top: Radius.circular(30),
),
border: Border(
top: BorderSide(
color: AppColors.lime,
width: 7,
),
),
),
child: Column(
crossAxisAlignment: CrossAxisAlignment.start,
children: [
const Center(
child: Text(
'Ingresa a tu cuenta',
textAlign: TextAlign.center,
style: TextStyle(
color: AppColors.cream,
fontSize: 24,
fontWeight: FontWeight.w800,
),
),
),
const SizedBox(height: 25),

const _FieldLabel('Correo'),
const SizedBox(height: 7),

_InputBox(
controller: emailController,
hint: 'hola@tucorreo.com',
icon: Icons.mail_outline,
keyboardType:
TextInputType.emailAddress,
onChanged: (_) {
if (showErrors) setState(() {});
},
),

if (showErrors && !emailIsValid) ...[
const SizedBox(height: 8),
const _ErrorChip(
text:
'Usa un correo válido ej: name@gmail.com',
),
],

const SizedBox(height: 16),

Row(
children: const [
_FieldLabel('Contraseña'),
Spacer(),
Icon(
Icons.lock_outline,
size: 15,
color: AppColors.cream,
),
SizedBox(width: 4),
Text(
'8+ caracteres',
style: TextStyle(
color: AppColors.cream,
fontSize: 13,
),
),
],
),
const SizedBox(height: 8),

_InputBox(
controller: passwordController,
hint: 'Crea una clave secreta',
icon: Icons.key_outlined,
obscure: !showPassword,
onChanged: (_) {
if (showErrors) setState(() {});
},
suffix: IconButton(
tooltip: showPassword
? 'Ocultar contraseña'
    : 'Mostrar contraseña',
onPressed: () => setState(
() => showPassword = !showPassword,
),
icon: Icon(
showPassword
? Icons.visibility_off_outlined
    : Icons.visibility_outlined,
color: AppColors.wine,
size: 19,
),
),
),

// Error ubicado justo debajo de la contraseña
if (showErrors &&
passwordController.text.isEmpty) ...[
const SizedBox(height: 8),
const _ErrorChip(
text: 'Ingresa tu contraseña',
),
],

Align(
alignment: Alignment.centerRight,
child: TextButton(
onPressed: recoverPassword,
child: const Text(
'Olvidé mi contraseña',
style: TextStyle(
color: AppColors.cream,
fontSize: 12,
decoration: TextDecoration.underline,
decorationColor: AppColors.cream,
),
),
),
),

const SizedBox(height: 10),

Center(
child: _LimeButton(
text: isLoading
? 'Ingresando...'
    : 'Entrar a mi Finagotchi',
onTap: isLoading ? () {} : login,
),
),
const SizedBox(height: 16),

Center(
child: Wrap(
alignment: WrapAlignment.center,
children: [
const Text(
'¿No tienes cuenta? ',
style: TextStyle(
color: AppColors.cream,
fontSize: 12,
),
),
GestureDetector(
onTap: () {
if (isLoading) return;

Navigator.push(
context,
MaterialPageRoute(
builder: (_) =>
const RegisterScreen(),
),
);
},
child: const Text(
'Regístrate',
style: TextStyle(
color: AppColors.cream,
fontSize: 11,
fontWeight: FontWeight.bold,
decoration:
TextDecoration.underline,
decorationColor: AppColors.cream,
),
),
),
],
),
),
],
),
),
],
),
),
);
},
),
),
);
}
}

class _RecoveryPanel extends StatefulWidget {
const _RecoveryPanel({required this.onSend});

final ValueChanged<String> onSend;

@override
State<_RecoveryPanel> createState() => _RecoveryPanelState();
}

class _RecoveryPanelState extends State<_RecoveryPanel> {
final controller = TextEditingController();

@override
void dispose() {
controller.dispose();
super.dispose();
}

@override
Widget build(BuildContext context) {
return Container(
width: double.infinity,
padding: EdgeInsets.fromLTRB(
24,
20,
24,
20 + MediaQuery.of(context).viewInsets.bottom,
),
decoration: const BoxDecoration(
color: AppColors.cream,
borderRadius: BorderRadius.vertical(
top: Radius.circular(28),
),
),
child: SingleChildScrollView(
child: Column(
crossAxisAlignment: CrossAxisAlignment.stretch,
children: [
Row(
children: [
Container(
padding: const EdgeInsets.symmetric(
horizontal: 12,
vertical: 7,
),
decoration: BoxDecoration(
color: const Color(0xFFF7E5CF),
borderRadius: BorderRadius.circular(20),
),
child: const Text(
'◉  Recuperar acceso',
style: TextStyle(
color: AppColors.wine,
fontSize: 11,
fontWeight: FontWeight.w600,
),
),
),
const Spacer(),
IconButton(
onPressed: () => Navigator.pop(context),
icon: const Icon(
Icons.close,
color: AppColors.wine,
),
),
],
),
const SizedBox(height: 25),
const Text(
'¿Olvidaste tu clave?',
textAlign: TextAlign.center,
style: TextStyle(
color: AppColors.darkGreen,
fontSize: 22,
fontWeight: FontWeight.w800,
),
),
const SizedBox(height: 18),
const Text(
'Tranqui, escribe el correo con el que te registraste '
'a tu Nancy y te mandamos un enlace para que crees '
'una nueva clave de una.',
textAlign: TextAlign.center,
style: TextStyle(
color: AppColors.darkGreen,
fontSize: 12,
height: 1.4,
),
),
const SizedBox(height: 28),
const Text(
'Correo registrado',
style: TextStyle(
color: AppColors.darkGreen,
fontWeight: FontWeight.w600,
fontSize: 13,
),
),
const SizedBox(height: 8),
_InputBox(
controller: controller,
hint: 'hola@tucorreo.com',
icon: Icons.mail_outline,
keyboardType: TextInputType.emailAddress,
),
const SizedBox(height: 22),
Center(
child: _LimeButton(
text: 'Enviar enlace',
onTap: () => widget.onSend(controller.text),
),
),
const SizedBox(height: 15),
Center(
child: Wrap(
alignment: WrapAlignment.center,
children: [
const Text(
'¿Te acordaste? ',
style: TextStyle(
color: AppColors.wine,
fontSize: 11,
),
),
GestureDetector(
onTap: () => Navigator.pop(context),
child: const Text(
'Volver a ingresar',
style: TextStyle(
color: AppColors.wine,
fontSize: 11,
fontWeight: FontWeight.bold,
decoration: TextDecoration.underline,
),
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
}

class _FieldLabel extends StatelessWidget {
const _FieldLabel(this.text);

final String text;

@override
Widget build(BuildContext context) {
return Text(
text,
style: const TextStyle(
color: AppColors.cream,
fontSize: 13,
fontWeight: FontWeight.w600,
),
);
}
}

class _InputBox extends StatelessWidget {
const _InputBox({
required this.controller,
required this.hint,
required this.icon,
this.obscure = false,
this.suffix,
this.keyboardType,
this.onChanged,
});

final TextEditingController controller;
final String hint;
final IconData icon;
final bool obscure;
final Widget? suffix;
final TextInputType? keyboardType;
final ValueChanged<String>? onChanged;

@override
Widget build(BuildContext context) {
return Container(
constraints: const BoxConstraints(minHeight: 48),
decoration: BoxDecoration(
color: AppColors.cream,
borderRadius: BorderRadius.circular(25),
border: const Border(
bottom: BorderSide(
color: AppColors.darkGreen,
width: 3,
),
),
),
child: TextField(
controller: controller,
obscureText: obscure,
keyboardType: keyboardType,
onChanged: onChanged,
style: const TextStyle(
color: AppColors.darkGreen,
fontSize: 14,
),
decoration: InputDecoration(
hintText: hint,
hintStyle: const TextStyle(
color: Color(0xFFB8B6C2),
fontSize: 12,
),
prefixIcon: Icon(
icon,
color: AppColors.wine,
size: 18,
),
suffixIcon: suffix,
prefixIconConstraints:
const BoxConstraints(minWidth: 40),
border: InputBorder.none,
contentPadding:
const EdgeInsets.symmetric(vertical: 14),
),
),
);
}
}

class _LimeButton extends StatelessWidget {
const _LimeButton({
required this.text,
required this.onTap,
});

final String text;
final VoidCallback onTap;

@override
Widget build(BuildContext context) {
return SizedBox(
height: 44,
child: ElevatedButton(
onPressed: onTap,
style: ElevatedButton.styleFrom(
backgroundColor: AppColors.lime,
foregroundColor: AppColors.darkGreen,
elevation: 0,
padding: const EdgeInsets.symmetric(horizontal: 20),
shape: const StadiumBorder(),
),
child: Row(
mainAxisSize: MainAxisSize.min,
children: [
Text(
text,
style: const TextStyle(
fontSize: 13,
fontWeight: FontWeight.w800,
),
),
const SizedBox(width: 10),
const Icon(
Icons.arrow_forward,
size: 17,
),
],
),
),
);
}
}

class _ErrorChip extends StatelessWidget {
const _ErrorChip({required this.text});

final String text;

@override
Widget build(BuildContext context) {
return Container(
padding: const EdgeInsets.symmetric(
horizontal: 10,
vertical: 6,
),
decoration: BoxDecoration(
color: AppColors.cream,
borderRadius: BorderRadius.circular(20),
),
child: Row(
mainAxisSize: MainAxisSize.min,
children: [
const Icon(
Icons.cancel,
color: Color(0xFFFF9800),
size: 13,
),
const SizedBox(width: 5),
Flexible(
child: Text(
text,
style: const TextStyle(
color: Color(0xFFB76B00),
fontSize: 10,
),
),
),
],
),
);
}
}
