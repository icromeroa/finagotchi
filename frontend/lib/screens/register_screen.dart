import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import 'login_screen.dart';
import 'onboarding/consent_screen.dart';
import 'onboarding/device_link_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();

  bool showPassword = false;
  bool acceptedTerms = false;
  bool showErrors = false;

  @override
  void dispose() {
    nameController.dispose();
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  bool get validEmail =>
      RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
          .hasMatch(emailController.text.trim());

  bool get hasEightCharacters =>
      passwordController.text.length >= 8;

  bool get hasNumber =>
      RegExp(r'\d').hasMatch(passwordController.text);

  bool get hasSpecialCharacter =>
      RegExp(r'[^a-zA-Z0-9]').hasMatch(passwordController.text);

  void register() {
    setState(() => showErrors = true);

    if (nameController.text.trim().isEmpty ||
        !validEmail ||
        !hasEightCharacters ||
        !hasNumber ||
        !hasSpecialCharacter ||
        !acceptedTerms) {
      return;
    }

    // Navegación hacia la pantalla de vinculación del dispositivo
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => const DeviceLinkScreen(),
      ),
    );
  }

  void _message(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.wine,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(27, 12, 27, 24),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight - 36,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Cabeza de Nancy
                    SizedBox(
                      height: 190,
                      child: Center(
                        child: Image.asset(
                          'assets/images/cabeza.png',
                          height: 180,
                          width: 280,
                          fit: BoxFit.contain,
                          filterQuality: FilterQuality.none,
                        ),
                      ),
                    ),

                    const SizedBox(height: 5),
                    const Text(
                      'Crea tu cuenta',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.cream,
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 16),

                    Row(
                      children: [
                        Expanded(
                          child: _SocialButton(
                            label: 'Google',
                            onTap: () => _message(
                              'Registro con Google próximamente.',
                            ),
                          ),
                        ),
                        const SizedBox(width: 15),
                        Expanded(
                          child: _SocialButton(
                            label: 'Apple',
                            apple: true,
                            onTap: () => _message(
                              'Registro con Apple próximamente.',
                            ),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 15),
                    const Text(
                      'o con tu correo:',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.cream,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(height: 25),

                    Row(
                      children: [
                        const _FieldLabel('Tu nombre'),
                        const Spacer(),
                        const Flexible(
                          child: Text(
                            '¿Cómo te llamará Nancy?',
                            textAlign: TextAlign.right,
                            style: TextStyle(
                              color: AppColors.cream,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 7),

                    _InputBox(
                      controller: nameController,
                      hint: 'Ej. Irene',
                      icon: Icons.sentiment_satisfied_alt_outlined,
                      onChanged: (_) {
                        if (showErrors) setState(() {});
                      },
                    ),

                    if (showErrors &&
                        nameController.text.trim().isEmpty) ...[
                      const SizedBox(height: 7),
                      const _NoticeChip(
                        text: 'Completa este espacio',
                        error: true,
                      ),
                    ],

                    const SizedBox(height: 16),
                    const _FieldLabel('Correo'),
                    const SizedBox(height: 7),

                    _InputBox(
                      controller: emailController,
                      hint: 'hola@tucorreo.com',
                      icon: Icons.mail_outline,
                      keyboardType: TextInputType.emailAddress,
                      onChanged: (_) {
                        if (showErrors) setState(() {});
                      },
                    ),

                    if (showErrors && !validEmail) ...[
                      const SizedBox(height: 7),
                      const _NoticeChip(
                        text: 'Usa un correo válido ej: name@gmail.com',
                        error: true,
                      ),
                    ],

                    const SizedBox(height: 16),
                    Row(
                      children: [
                        const _FieldLabel('Contraseña'),
                        const Spacer(),
                        const Icon(
                          Icons.lock_outline,
                          size: 13,
                          color: AppColors.cream,
                        ),
                        const SizedBox(width: 4),
                        const Text(
                          '8+ caracteres',
                          style: TextStyle(
                            color: AppColors.cream,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 7),

                    _InputBox(
                      controller: passwordController,
                      hint: 'Crea una clave secreta',
                      icon: Icons.key_outlined,
                      obscure: !showPassword,
                      onChanged: (_) => setState(() {}),
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

                    if (passwordController.text.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 7,
                        runSpacing: 7,
                        children: [
                          _NoticeChip(
                            text: '8+ caracteres',
                            error: !hasEightCharacters,
                          ),
                          _NoticeChip(
                            text: '1 número',
                            error: !hasNumber,
                          ),
                          _NoticeChip(
                            text: '1 carácter especial',
                            error: !hasSpecialCharacter,
                          ),
                        ],
                      ),
                    ],

                    if (showErrors &&
                        passwordController.text.isEmpty) ...[
                      const SizedBox(height: 7),
                      const _NoticeChip(
                        text: 'Escribe una contraseña',
                        error: true,
                      ),
                    ],

                    const SizedBox(height: 17),

                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        SizedBox(
                          width: 28,
                          height: 36,
                          child: Checkbox(
                            value: acceptedTerms,
                            onChanged: (value) => setState(
                                  () => acceptedTerms = value ?? false,
                            ),
                            activeColor: AppColors.lime,
                            checkColor: AppColors.darkGreen,
                            side: const BorderSide(
                              color: AppColors.cream,
                              width: 1,
                            ),
                            materialTapTargetSize:
                            MaterialTapTargetSize.shrinkWrap,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Wrap(
                            children: [
                              const Text(
                                'Acepto los ',
                                style: TextStyle(
                                  color: AppColors.cream,
                                  fontSize: 10,
                                ),
                              ),
                              _legalLink('Términos'),
                              const Text(
                                ' y la ',
                                style: TextStyle(
                                  color: AppColors.cream,
                                  fontSize: 10,
                                ),
                              ),
                              _legalLink('Política de Privacidad'),
                              const Text(
                                ' de FinaGotchi.',
                                style: TextStyle(
                                  color: AppColors.cream,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),

                    if (showErrors && !acceptedTerms) ...[
                      const SizedBox(height: 5),
                      const _NoticeChip(
                        text: 'Debes aceptar los términos',
                        error: true,
                      ),
                    ],

                    const SizedBox(height: 22),
                    Center(
                      child: _LimeButton(
                        text: '¡Empezar con Nancy!',
                        onTap: register,
                      ),
                    ),
                    const SizedBox(height: 17),

                    Center(
                      child: Wrap(
                        alignment: WrapAlignment.center,
                        children: [
                          const Text(
                            '¿Ya tienes cuenta? ',
                            style: TextStyle(
                              color: AppColors.cream,
                              fontSize: 11,
                            ),
                          ),
                          GestureDetector(
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => const LoginScreen(),
                                ),
                              );
                            },
                            child: const Text(
                              'Inicia sesión',
                              style: TextStyle(
                                color: AppColors.cream,
                                fontSize: 11,
                                decoration: TextDecoration.underline,
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
            );
          },
        ),
      ),
    );
  }

  Widget _legalLink(String text) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => const ConsentScreen(),
          ),
        );
      },
      child: Text(
        text,
        style: const TextStyle(
          color: AppColors.lime,
          fontSize: 10,
          decoration: TextDecoration.underline,
          decorationColor: AppColors.lime,
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
    return Text(text, style: const TextStyle(color: AppColors.cream, fontSize: 13, fontWeight: FontWeight.w600));
  }
}

class _SocialButton extends StatelessWidget {
  const _SocialButton({required this.label, required this.onTap, this.apple = false});
  final String label;
  final VoidCallback onTap;
  final bool apple;
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40,
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(backgroundColor: AppColors.cream, foregroundColor: AppColors.wine, elevation: 0, padding: const EdgeInsets.symmetric(horizontal: 8), shape: const StadiumBorder()),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (apple) const Icon(Icons.phone_iphone, size: 17, color: Colors.black)
            else const Text('G', style: TextStyle(color: Color(0xFF4285F4), fontSize: 18, fontWeight: FontWeight.w900)),
            const SizedBox(width: 7),
            Text(label, style: const TextStyle(fontSize: 11)),
          ],
        ),
      ),
    );
  }
}

class _InputBox extends StatelessWidget {
  const _InputBox({required this.controller, required this.hint, required this.icon, this.obscure = false, this.suffix, this.keyboardType, this.onChanged});
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
      decoration: BoxDecoration(color: AppColors.cream, borderRadius: BorderRadius.circular(25), border: const Border(bottom: BorderSide(color: AppColors.darkGreen, width: 3))),
      child: TextField(
        controller: controller, obscureText: obscure, keyboardType: keyboardType, onChanged: onChanged,
        style: const TextStyle(color: AppColors.darkGreen, fontSize: 14),
        decoration: InputDecoration(hintText: hint, hintStyle: const TextStyle(color: Color(0xFFB8B6C2), fontSize: 12), prefixIcon: Icon(icon, color: AppColors.wine, size: 18), suffixIcon: suffix, prefixIconConstraints: const BoxConstraints(minWidth: 40), border: InputBorder.none, contentPadding: const EdgeInsets.symmetric(vertical: 14)),
      ),
    );
  }
}

class _LimeButton extends StatelessWidget {
  const _LimeButton({required this.text, required this.onTap});
  final String text;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44,
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(backgroundColor: AppColors.lime, foregroundColor: AppColors.darkGreen, elevation: 0, padding: const EdgeInsets.symmetric(horizontal: 20), shape: const StadiumBorder()),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(text, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
            const SizedBox(width: 10),
            const Icon(Icons.arrow_forward, size: 17),
          ],
        ),
      ),
    );
  }
}

class _NoticeChip extends StatelessWidget {
  const _NoticeChip({required this.text, required this.error});
  final String text;
  final bool error;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(color: AppColors.cream, borderRadius: BorderRadius.circular(20)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(error ? Icons.cancel : Icons.check_circle, color: error ? const Color(0xFFFF9800) : AppColors.lime, size: 13),
          const SizedBox(width: 5),
          Flexible(child: Text(text, style: TextStyle(color: error ? const Color(0xFFB76B00) : AppColors.darkGreen, fontSize: 10))),
        ],
      ),
    );
  }
}