import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

// ===================================================================
// 1. PANTALLA DE ADVERTENCIA PREVIA
// ===================================================================
class DeleteAccountScreen extends StatefulWidget {
  const DeleteAccountScreen({super.key});

  @override
  State<DeleteAccountScreen> createState() => _DeleteAccountScreenState();
}

class _DeleteAccountScreenState extends State<DeleteAccountScreen> {
  bool _donarDatosAnonimos = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // Barra superior
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, color: AppColors.wine, size: 20),
                  const SizedBox(width: 8),
                  const Text(
                    'Eliminar mi cuenta',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 16,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Container(
                      width: 34,
                      height: 34,
                      decoration: const BoxDecoration(
                        color: AppColors.mutedPink,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.close, color: AppColors.wine, size: 18),
                    ),
                  ),
                ],
              ),
            ),

            // Contenido con scroll
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    // Icono de advertencia central
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: const BoxDecoration(
                        color: AppColors.mutedPink,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.warning_amber_rounded, color: AppColors.wine, size: 32),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      '¿Seguro que quieres\nirte?',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.wine,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 10),
                      child: Text(
                        'Eliminar tu cuenta borra tus datos y a Nancy. Primero mira qué pasa y, si prefieres, guarda una copia.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: AppColors.darkGreen,
                          fontSize: 12,
                          height: 1.3,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Tarjeta: Esto se borra para siempre
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.delete_outline, color: AppColors.wine, size: 18),
                              SizedBox(width: 8),
                              Text(
                                'Esto se borra para siempre',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13.5,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          _buildDeleteRow('Movimientos', '66'),
                          _buildDeleteRow('Cuentas', '6'),
                          _buildDeleteRow('Categorías propias', '1'),
                          _buildDeleteRow('Gastos fijos', '5'),
                          _buildDeleteRow('Metas de ahorro', '2 · \$650.000'),
                          _buildDeleteRow('Presupuesto', '1'),
                          const SizedBox(height: 10),
                          // Subtarjeta interna rosa
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: AppColors.mutedPink.withOpacity(0.5),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(
                              children: const [
                                Icon(Icons.pets, color: AppColors.wine, size: 18),
                                SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'También se borran Nancy, tu progreso y tus avisos.',
                                    style: TextStyle(
                                      color: AppColors.wine,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Tarjeta: Tu FinaGotchi se desvincula
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.mutedPink,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(Icons.devices, color: AppColors.wine, size: 20),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Tu FinaGotchi se desvincula',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12.5,
                                  ),
                                ),
                                Text(
                                  'Vuelve a su estado de fábrica. Podrás vincularlo a otra cuenta.',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 10.5,
                                    height: 1.2,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Tarjeta verde: Tienes 14 días para arrepentirte
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.lime.withOpacity(0.85),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppColors.darkGreen.withOpacity(0.2)),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: const BoxDecoration(
                              color: AppColors.darkGreen,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.calendar_today_outlined, color: AppColors.lime, size: 18),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Tienes 14 días para arrepentirte',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontWeight: FontWeight.w900,
                                    fontSize: 12.5,
                                  ),
                                ),
                                Text(
                                  'Si inicias sesión antes del 1 de diciembre, recuperas todo.',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 10.5,
                                    height: 1.2,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Switch: Conservar mis datos sin nombre para el estudio
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Conservar mis datos sin nombre para el estudio',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'Sin tu nombre ni tu contacto. Ayuda a mejorar FinaGotchi.',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 10,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Switch(
                            value: _donarDatosAnonimos,
                            onChanged: (val) {
                              setState(() {
                                _donarDatosAnonimos = val;
                              });
                            },
                            activeColor: AppColors.cardCream,
                            activeTrackColor: AppColors.lime,
                            inactiveThumbColor: AppColors.cardCream,
                            inactiveTrackColor: Colors.grey.shade300,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Botón principal: Mantener mi cuenta
                    Center(
                      child: Container(
                        height: 50,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: AppColors.lime,
                          borderRadius: BorderRadius.circular(25),
                          border: const Border(
                            bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
                          ),
                        ),
                        child: InkWell(
                          onTap: () => Navigator.pop(context),
                          borderRadius: BorderRadius.circular(25),
                          child: const Center(
                            child: Text(
                              'Mantener mi cuenta',
                              style: TextStyle(
                                color: AppColors.darkGreen,
                                fontWeight: FontWeight.w900,
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Botón inferior: Continuar con la eliminación
                    Center(
                      child: TextButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const DeleteAccountConfirmScreen(),
                            ),
                          );
                        },
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Icon(Icons.delete_outline, color: AppColors.wine, size: 16),
                            SizedBox(width: 6),
                            Text(
                              'Continuar con la eliminación',
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
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDeleteRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const Icon(Icons.circle, size: 6, color: AppColors.darkGreen),
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          Text(
            value,
            style: const TextStyle(
              color: AppColors.wine,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}


// ===================================================================
// 2. PANTALLA DE CONFIRMACIÓN FINAL
// ===================================================================
class DeleteAccountConfirmScreen extends StatefulWidget {
  const DeleteAccountConfirmScreen({super.key});

  @override
  State<DeleteAccountConfirmScreen> createState() => _DeleteAccountConfirmScreenState();
}

class _DeleteAccountConfirmScreenState extends State<DeleteAccountConfirmScreen> {
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmTextController = TextEditingController();
  bool _isCheckboxChecked = false;
  bool _obscurePassword = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  const Text(
                    'V18 Eliminar Perfil definitivo',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Container(
                      width: 34,
                      height: 34,
                      decoration: const BoxDecoration(
                        color: AppColors.mutedPink,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.close, color: AppColors.wine, size: 20),
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.warning_amber_rounded, color: AppColors.wine, size: 24),
                        SizedBox(width: 8),
                        Text(
                          'Eliminar mi cuenta',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 20,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    // Contenedor superior con tono beige (cardCream) idéntico a la imagen
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: Column(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: const BoxDecoration(
                              color: AppColors.mutedPink,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.warning_amber_rounded, color: AppColors.wine, size: 28),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'Último paso',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 16,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Confirma que eres tú para programar la eliminación definitiva de Nancy y tu cuenta.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 12,
                              height: 1.3,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      'Tu contraseña',
                      style: TextStyle(
                        color: AppColors.wine,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: TextField(
                        controller: _passwordController,
                        obscureText: _obscurePassword,
                        style: const TextStyle(
                          color: AppColors.wine,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                        decoration: InputDecoration(
                          hintText: 'Introduce tu contraseña actual',
                          hintStyle: TextStyle(color: AppColors.darkGreen.withOpacity(0.5), fontSize: 13),
                          suffixIcon: IconButton(
                            icon: Icon(
                              _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                              color: AppColors.wine,
                              size: 20,
                            ),
                            onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                          ),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Escribe ELIMINAR para continuar',
                      style: TextStyle(
                        color: AppColors.wine,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                      ),
                      child: TextField(
                        controller: _confirmTextController,
                        style: const TextStyle(
                          color: AppColors.wine,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                        decoration: InputDecoration(
                          hintText: 'ELIMINAR',
                          hintStyle: TextStyle(color: AppColors.darkGreen.withOpacity(0.4), fontSize: 13),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        SizedBox(
                          height: 24,
                          width: 24,
                          child: Checkbox(
                            value: _isCheckboxChecked,
                            activeColor: AppColors.wine,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                            onChanged: (val) {
                              setState(() {
                                _isCheckboxChecked = val ?? false;
                              });
                            },
                          ),
                        ),
                        const SizedBox(width: 10),
                        const Expanded(
                          child: Text(
                            'Entiendo que mis datos se borrarán pasados 14 días',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontSize: 11.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    // Botón principal "Eliminar mi cuenta" en color vino/tinto
                    Center(
                      child: Container(
                        height: 52,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: AppColors.wine,
                          borderRadius: BorderRadius.circular(26),
                          border: Border(
                            bottom: BorderSide(color: AppColors.wine.withOpacity(0.8), width: 3.5),
                          ),
                        ),
                        child: InkWell(
                          onTap: () {},
                          borderRadius: BorderRadius.circular(26),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: const [
                              Icon(Icons.delete_outline, color: AppColors.cardCream, size: 20),
                              SizedBox(width: 8),
                              Text(
                                'Eliminar mi cuenta',
                                style: TextStyle(
                                  color: AppColors.cardCream,
                                  fontWeight: FontWeight.w900,
                                  fontSize: 15,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Center(
                      child: GestureDetector(
                        onTap: () => Navigator.pop(context),
                        child: const Text(
                          'Volver',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                            decoration: TextDecoration.underline,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppColors.wine.withOpacity(0.12)),
                      ),
                      child: Row(
                        children: const [
                          Icon(Icons.info_outline, color: AppColors.wine, size: 20),
                          SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Tienes un periodo de gracia de 14 días para reactivar tu perfil iniciando sesión antes del borrado irreversible.',
                              style: TextStyle(
                                color: AppColors.darkGreen,
                                fontSize: 11,
                                height: 1.3,
                              ),
                            ),
                          ),
                        ],
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
}