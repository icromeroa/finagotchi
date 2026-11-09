
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/finagotchi_dialogs.dart';

class PersonalDataScreen extends StatefulWidget {
  const PersonalDataScreen({super.key});

  @override
  State<PersonalDataScreen> createState() => _PersonalDataScreenState();
}

class _PersonalDataScreenState extends State<PersonalDataScreen> {
  // Controladores de texto con los datos actuales del usuario
  final TextEditingController _nameController =
  TextEditingController(text: 'Camilo Restrepo');

  final TextEditingController _emailController =
  TextEditingController(text: 'camilo.finanzas@correo.com');

  final TextEditingController _phoneController =
  TextEditingController(text: '+57 300 123 4567');

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(30),
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // BARRA SUPERIOR (Botón cerrar)
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    width: 32,
                    height: 32,
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

            const SizedBox(height: 2),

            // CABECERA
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.badge_outlined,
                    color: AppColors.wine,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 10),
                const Text(
                  'Datos Personales',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 4),

            const Padding(
              padding: EdgeInsets.only(left: 2),
              child: Text(
                'Actualiza cómo te conoce Nancy en tu aventura',
                style: TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 12,
                ),
              ),
            ),

            const SizedBox(height: 16),

            // NOMBRE COMPLETO
            const Text(
              'Nombre Completo *',
              style: TextStyle(
                color: AppColors.wine,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),

            const SizedBox(height: 4),

            _buildTextField(
              controller: _nameController,
              icon: Icons.person_outline,
            ),

            const SizedBox(height: 12),

            // CORREO ELECTRÓNICO
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Correo Electrónico *',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),

                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.lime,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: const [
                      Icon(
                        Icons.check_circle,
                        color: AppColors.darkGreen,
                        size: 12,
                      ),
                      SizedBox(width: 4),
                      Text(
                        'Verificado',
                        style: TextStyle(
                          color: AppColors.darkGreen,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 4),

            _buildTextField(
              controller: _emailController,
              icon: Icons.mail_outline,
            ),

            const SizedBox(height: 12),

            // TELÉFONO
            const Text(
              'Teléfono Móvil',
              style: TextStyle(
                color: AppColors.wine,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),

            const SizedBox(height: 4),

            _buildTextField(
              controller: _phoneController,
              icon: Icons.phone_android_outlined,
            ),

            const SizedBox(height: 14),

            // TARJETA INFORMATIVA DE NANCY
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.mutedPink.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: AppColors.wine.withValues(alpha: 0.12),
                ),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: const BoxDecoration(
                      color: AppColors.cardCream,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.lightbulb_outline,
                      color: AppColors.wine,
                      size: 20,
                    ),
                  ),

                  const SizedBox(width: 10),

                  Expanded(
                    child: RichText(
                      text: const TextSpan(
                        style: TextStyle(
                          color: AppColors.wine,
                          fontSize: 11.5,
                          height: 1.25,
                        ),
                        children: [
                          TextSpan(
                            text: 'Nancy usará tu nombre ',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          TextSpan(
                            text:
                            'en los saludos diarios, reportes matutinos y retos de ahorro que compartan.',
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // BOTÓN GUARDAR CAMBIOS
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  FinaGotchiDialogs.showSaved(context);
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.lime,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(24),
                    side: const BorderSide(
                      color: AppColors.darkGreen,
                      width: 1.5,
                    ),
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: const [
                    Icon(
                      Icons.save_outlined,
                      color: AppColors.darkGreen,
                      size: 18,
                    ),
                    SizedBox(width: 6),
                    Text(
                      'Guardar Cambios',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontWeight: FontWeight.w900,
                        fontSize: 14.5,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 4),

            // CANCELAR
            Center(
              child: GestureDetector(
                onTap: () => Navigator.pop(context),
                child: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8.0),
                  child: Text(
                    'Cancelar',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // CONSTRUCTOR DE CAMPOS DE TEXTO
  Widget _buildTextField({
    required TextEditingController controller,
    required IconData icon,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AppColors.wine.withValues(alpha: 0.15),
        ),
      ),
      child: TextField(
        controller: controller,
        style: const TextStyle(
          color: AppColors.wine,
          fontWeight: FontWeight.bold,
          fontSize: 13.5,
        ),
        decoration: InputDecoration(
          prefixIcon: Icon(
            icon,
            color: AppColors.wine,
            size: 18,
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
