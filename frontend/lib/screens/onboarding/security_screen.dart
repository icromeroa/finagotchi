import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

class SecurityScreen extends StatefulWidget {
  const SecurityScreen({super.key});

  @override
  State<SecurityScreen> createState() => _SecurityScreenState();
}

class _SecurityScreenState extends State<SecurityScreen> {
  final TextEditingController _currentPasswordController =
  TextEditingController(text: 'MiClaveSegura123!');

  final TextEditingController _newPasswordController =
  TextEditingController(text: 'NancySuperProgres0\$2024');

  final TextEditingController _confirmPasswordController =
  TextEditingController(text: 'NancySuperProgres0\$2024');

  bool _obscureCurrent = false;
  bool _obscureNew = false;

  // Evalúa la contraseña nueva
  int get _strengthScore {
    final password = _newPasswordController.text;
    int score = 0;

    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (RegExp(r'[0-9]').hasMatch(password)) score++;
    if (RegExp(r'[^\w\s]').hasMatch(password)) score++;

    if (RegExp(r'[A-Z]').hasMatch(password) &&
        RegExp(r'[a-z]').hasMatch(password)) {
      score++;
    }

    return score;
  }

  // Nombre del nivel de seguridad
  String get _strengthLabel {
    if (_strengthScore <= 1) {
      return 'Débil';
    } else if (_strengthScore <= 3) {
      return 'Puede mejorar';
    } else {
      return 'Fuerte';
    }
  }

  // Color del nivel de seguridad
  Color get _strengthColor {
    if (_strengthScore <= 1) {
      return AppColors.wine;
    } else if (_strengthScore <= 3) {
      return Colors.orange;
    } else {
      return AppColors.lime;
    }
  }

  // Cantidad de segmentos encendidos
  int get _strengthSegments {
    if (_strengthScore <= 1) {
      return 1;
    } else if (_strengthScore <= 3) {
      return 2;
    } else {
      return 3;
    }
  }

  // Método para mostrar el modal de éxito
  void _showSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return Dialog(
          backgroundColor: AppColors.cardCream,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
            side: BorderSide(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Icono superior de éxito (Icono circular verde con flechas de actualización y check)
                Stack(
                  alignment: Alignment.bottomRight,
                  children: [
                    Container(
                      width: 70,
                      height: 70,
                      decoration: const BoxDecoration(
                        color: AppColors.lime,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.sync,
                        color: AppColors.darkGreen,
                        size: 36,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.all(2),
                      decoration: const BoxDecoration(
                        color: AppColors.cardCream,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.check_circle,
                        color: Colors.green,
                        size: 22,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),

                // Título
                const Text(
                  'Se ha actualizado con\néxito',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: AppColors.wine,
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 8),

                // Subtítulo
                const Text(
                  'Ya ves la información al día.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 12.5,
                  ),
                ),
                const SizedBox(height: 24),

                // Botón Entendido
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context); // Cierra el diálogo
                      Navigator.pop(context); // Cierra la pantalla de seguridad
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.lime,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(24),
                      ),
                      side: const BorderSide(
                        color: AppColors.darkGreen,
                        width: 2,
                      ),
                    ),
                    child: const Text(
                      'Entendido',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontWeight: FontWeight.w900,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  void dispose() {
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black54,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: const EdgeInsets.only(top: 40),
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    maxHeight: constraints.maxHeight - 40,
                  ),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.fromLTRB(20, 12, 20, 4),
                    decoration: const BoxDecoration(
                      color: AppColors.cream,
                      borderRadius: BorderRadius.vertical(
                        top: Radius.circular(30),
                      ),
                    ),
                    child: SingleChildScrollView(
                      physics: const BouncingScrollPhysics(),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Pestaña superior
                          Center(
                            child: Container(
                              width: 36,
                              height: 4,
                              decoration: BoxDecoration(
                                color: AppColors.mutedPink,
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                          ),

                          const SizedBox(height: 12),

                          // Título y botón cerrar
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        const Icon(
                                          Icons.lock_outline,
                                          color: AppColors.wine,
                                          size: 22,
                                        ),
                                        const SizedBox(width: 8),
                                        const Text(
                                          'Cambiar Contraseña',
                                          style: TextStyle(
                                            color: AppColors.wine,
                                            fontSize: 20,
                                            fontWeight: FontWeight.w900,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 4),
                                    const Text(
                                      'Protege tu alcancía y tus progresos con Nancy',
                                      style: TextStyle(
                                        color: AppColors.darkGreen,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              GestureDetector(
                                onTap: () => Navigator.pop(context),
                                child: Container(
                                  width: 34,
                                  height: 34,
                                  decoration: const BoxDecoration(
                                    color: AppColors.mutedPink,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(
                                    Icons.close,
                                    color: AppColors.wine,
                                    size: 18,
                                  ),
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(height: 16),

                          // Contraseña actual
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text(
                                'Contraseña Actual',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12.5,
                                ),
                              ),
                              Row(
                                children: const [
                                  Icon(
                                    Icons.shield_outlined,
                                    color: AppColors.darkGreen,
                                    size: 13,
                                  ),
                                  SizedBox(width: 3),
                                  Text(
                                    'Verificada',
                                    style: TextStyle(
                                      color: AppColors.darkGreen,
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),

                          const SizedBox(height: 6),

                          _buildPasswordField(
                            controller: _currentPasswordController,
                            obscureText: _obscureCurrent,
                            onToggle: () {
                              setState(() {
                                _obscureCurrent = !_obscureCurrent;
                              });
                            },
                          ),

                          const SizedBox(height: 12),

                          // Nueva contraseña
                          const Text(
                            'Nueva Contraseña',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 12.5,
                            ),
                          ),

                          const SizedBox(height: 6),

                          _buildPasswordField(
                            controller: _newPasswordController,
                            obscureText: _obscureNew,
                            onChanged: (value) {
                              setState(() {});
                            },
                            onToggle: () {
                              setState(() {
                                _obscureNew = !_obscureNew;
                              });
                            },
                          ),

                          const SizedBox(height: 8),

                          // Indicador interactivo de seguridad
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: AppColors.cardCream,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: AppColors.wine.withOpacity(0.12),
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment:
                                  MainAxisAlignment.spaceBetween,
                                  children: [
                                    Row(
                                      children: const [
                                        Icon(
                                          Icons.bolt,
                                          color: Colors.orange,
                                          size: 15,
                                        ),
                                        SizedBox(width: 4),
                                        Text(
                                          'Nivel de seguridad',
                                          style: TextStyle(
                                            color: AppColors.wine,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 11,
                                          ),
                                        ),
                                      ],
                                    ),
                                    AnimatedSwitcher(
                                      duration:
                                      const Duration(milliseconds: 250),
                                      child: Text(
                                        _strengthLabel,
                                        key: ValueKey(_strengthLabel),
                                        style: TextStyle(
                                          color: _strengthColor,
                                          fontWeight: FontWeight.w900,
                                          fontSize: 11.5,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Row(
                                  children: List.generate(3, (index) {
                                    final active =
                                        index < _strengthSegments;

                                    return Expanded(
                                      child: AnimatedContainer(
                                        duration:
                                        const Duration(milliseconds: 300),
                                        margin: EdgeInsets.only(
                                          right: index == 2 ? 0 : 6,
                                        ),
                                        height: 6,
                                        decoration: BoxDecoration(
                                          color: active
                                              ? _strengthColor
                                              : AppColors.progressBackground,
                                          borderRadius:
                                          BorderRadius.circular(3),
                                        ),
                                      ),
                                    );
                                  }),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 12),

                          // Confirmar nueva contraseña
                          const Text(
                            'Confirmar Nueva Contraseña',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 12.5,
                            ),
                          ),

                          const SizedBox(height: 6),

                          Container(
                            decoration: BoxDecoration(
                              color: AppColors.cardCream,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: AppColors.wine.withOpacity(0.12),
                              ),
                            ),
                            child: TextField(
                              controller: _confirmPasswordController,
                              obscureText: false,
                              style: const TextStyle(
                                color: AppColors.wine,
                                fontWeight: FontWeight.bold,
                                fontSize: 13.5,
                              ),
                              decoration: const InputDecoration(
                                prefixIcon: Icon(
                                  Icons.lock_outline,
                                  color: AppColors.wine,
                                  size: 18,
                                ),
                                suffixIcon: Icon(
                                  Icons.check_circle,
                                  color: Colors.green,
                                  size: 18,
                                ),
                                border: InputBorder.none,
                                contentPadding: EdgeInsets.symmetric(
                                  horizontal: 14,
                                  vertical: 12,
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(height: 12),

                          // Información de Nancy
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: AppColors.mutedPink.withOpacity(0.5),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: AppColors.wine.withOpacity(0.12),
                              ),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(7),
                                  decoration: const BoxDecoration(
                                    color: AppColors.cardCream,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(
                                    Icons.lightbulb_outline,
                                    color: AppColors.wine,
                                    size: 16,
                                  ),
                                ),
                                const SizedBox(width: 10),
                                const Expanded(
                                  child: Text(
                                    'Mínimo 8 caracteres, al menos un número y símbolo especial para mantener feliz a Nancy.',
                                    style: TextStyle(
                                      color: AppColors.wine,
                                      fontSize: 11,
                                      height: 1.3,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 14),

                          // Actualizar contraseña -> Llama al modal de éxito
                          SizedBox(
                            width: double.infinity,
                            height: 46,
                            child: ElevatedButton(
                              onPressed: _showSuccessDialog, // <--- Aquí se conecta
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.lime,
                                elevation: 0,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(23),
                                ),
                                side: const BorderSide(
                                  color: AppColors.darkGreen,
                                  width: 2,
                                ),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: const [
                                  Icon(
                                    Icons.vpn_key_outlined,
                                    color: AppColors.darkGreen,
                                    size: 18,
                                  ),
                                  SizedBox(width: 8),
                                  Text(
                                    'Actualizar Contraseña',
                                    style: TextStyle(
                                      color: AppColors.darkGreen,
                                      fontWeight: FontWeight.w900,
                                      fontSize: 14,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),

                          const SizedBox(height: 8),

                          // Recuperar contraseña
                          Center(
                            child: GestureDetector(
                              onTap: () {},
                              child: RichText(
                                text: const TextSpan(
                                  style: TextStyle(
                                    fontSize: 11.5,
                                    color: AppColors.darkGreen,
                                  ),
                                  children: [
                                    TextSpan(
                                      text:
                                      '¿Olvidaste tu contraseña actual? ',
                                    ),
                                    TextSpan(
                                      text: 'Recuperar aquí',
                                      style: TextStyle(
                                        color: AppColors.wine,
                                        fontWeight: FontWeight.bold,
                                        decoration:
                                        TextDecoration.underline,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(height: 2),

                          // Cancelar
                          Center(
                            child: TextButton(
                              onPressed: () => Navigator.pop(context),
                              style: TextButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                  vertical: 2,
                                  horizontal: 8,
                                ),
                                minimumSize: Size.zero,
                                tapTargetSize:
                                MaterialTapTargetSize.shrinkWrap,
                              ),
                              child: const Text(
                                'Cancelar',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  // Campo reutilizable de contraseña
  Widget _buildPasswordField({
    required TextEditingController controller,
    required bool obscureText,
    required VoidCallback onToggle,
    ValueChanged<String>? onChanged,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.12),
        ),
      ),
      child: TextField(
        controller: controller,
        obscureText: obscureText,
        onChanged: onChanged,
        style: const TextStyle(
          color: AppColors.wine,
          fontWeight: FontWeight.bold,
          fontSize: 13.5,
        ),
        decoration: InputDecoration(
          prefixIcon: const Icon(
            Icons.lock_outline,
            color: AppColors.wine,
            size: 18,
          ),
          suffixIcon: IconButton(
            icon: Icon(
              obscureText
                  ? Icons.visibility_off_outlined
                  : Icons.visibility_outlined,
              color: AppColors.wine,
              size: 18,
            ),
            onPressed: onToggle,
          ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 14,
            vertical: 12,
          ),
        ),
      ),
    );
  }
}