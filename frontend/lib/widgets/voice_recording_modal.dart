import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

// =========================================================================
// MAPA GLOBAL DE CATEGORÍAS Y DATOS
// =========================================================================
final Map<String, List> globalCategoriesByType = {
  'Gasto': [
    {'name': 'Alimentación', 'icon': Icons.restaurant},
    {'name': 'Transporte', 'icon': Icons.directions_bus},
    {'name': 'Ocio y gustos', 'icon': Icons.sports_esports},
    {'name': 'Deudas', 'icon': Icons.money_off},
    {'name': 'Familia', 'icon': Icons.favorite},
    {'name': 'Vivienda', 'icon': Icons.home},
    {'name': 'Salud y aseo', 'icon': Icons.medical_services},
    {'name': 'Suscripciones', 'icon': Icons.subscriptions},
    {'name': 'Crear', 'icon': Icons.add_circle_outline},
  ],
  'Ingreso': [
    {'name': 'Salario', 'icon': Icons.account_balance_wallet},
    {'name': 'Freelance', 'icon': Icons.card_travel},
    {'name': 'Beca', 'icon': Icons.school},
    {'name': 'Regalos', 'icon': Icons.card_giftcard},
    {'name': 'Inversión', 'icon': Icons.trending_up},
    {'name': 'Ventas', 'icon': Icons.store},
    {'name': 'Otros', 'icon': Icons.savings},
    {'name': 'Crear', 'icon': Icons.add_circle_outline},
  ],
  'Ahorro': [
    {
      'name': 'Viaje a Cartagena',
      'subtitle': 'Vacaciones soñadas',
      'current': 200000,
      'total': 800000,
      'progress': 0.25,
      'icon': Icons.flight
    },
    {
      'name': 'Teléfono nuevo',
      'subtitle': 'Tecnología y estudio',
      'current': 450000,
      'total': 1200000,
      'progress': 0.38,
      'tag': 'Vas bien',
      'icon': Icons.phone_android
    },
    {
      'name': 'Ahorro libre',
      'subtitle': 'Sin meta fija',
      'progress': 0.0,
      'icon': Icons.account_balance_wallet_outlined
    },
    {
      'name': 'Nueva meta',
      'subtitle': '',
      'progress': 0.0,
      'isAdd': true,
      'icon': Icons.add_circle_outline
    },
  ],
};

// =========================================================================
// FUNCIONES AUXILIARES PARA MOSTRAR LOS MODALES FÁCILMENTE
// =========================================================================
void showConfirmModal(BuildContext context) {
  Navigator.pop(context); // Cierra el modal actual
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (context) => const ConfirmDataModal(),
  );
}

void showErrorModal(BuildContext context, VoidCallback onTryAgain, VoidCallback onManualRegister) {
  Navigator.pop(context); // Cierra el modal actual
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (context) => VoiceErrorModal(
      onTryAgain: onTryAgain,
      onManualRegister: onManualRegister,
    ),
  );
}

// =========================================================================
// 1. MODAL GRABANDO (ACTIVO)
// =========================================================================
class VoiceRecordingModal extends StatelessWidget {
  final VoidCallback onSimulateError;
  final VoidCallback onSimulateSuccess;
  final VoidCallback onManualRegister;

  const VoiceRecordingModal({
    super.key,
    required this.onSimulateError,
    required this.onSimulateSuccess,
    required this.onManualRegister,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.mutedPink,
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              const Icon(Icons.mic, color: AppColors.wine, size: 22),
              const SizedBox(width: 8),
              const Text(
                'Grabando (activo)',
                style: TextStyle(
                  color: AppColors.wine,
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const Spacer(),
              InkWell(
                onTap: () => Navigator.pop(context),
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink.withOpacity(0.5),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.close, color: AppColors.wine, size: 18),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Chips de prueba superiores conectados para abrir ConfirmDataModal directamente
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildTestChip('Grabando', isSelected: true, onTap: null),
                const SizedBox(width: 8),
                _buildTestChip('No se escuchó (Error)', isSelected: false, onTap: onSimulateError),
                const SizedBox(width: 8),
                _buildTestChip('Confirmado (Éxito)', isSelected: false, onTap: () => showConfirmModal(context)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.25),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: AppColors.wine.withOpacity(0.4),
                width: 1.5,
              ),
            ),
            child: Center(
              child: Container(
                width: 45,
                height: 45,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withOpacity(0.4),
                  shape: BoxShape.circle,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Te escucho...',
            style: TextStyle(
              color: AppColors.wine,
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 16),
          Container(
            width: 75,
            height: 75,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.lime.withOpacity(0.3),
              border: Border.all(color: AppColors.darkGreen.withOpacity(0.2), width: 1.5),
            ),
            child: Center(
              child: Container(
                width: 52,
                height: 52,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.lime,
                ),
                child: const Icon(Icons.mic, color: AppColors.darkGreen, size: 26),
              ),
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'Suelta para enviar',
            style: TextStyle(
              color: AppColors.darkGreen,
              fontSize: 13,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 14),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              'Di, por ejemplo: “Almuerzo corriente 14 mil con Nequi”',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.darkGreen,
                fontSize: 11.5,
                height: 1.3,
              ),
            ),
          ),
          const SizedBox(height: 20),
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
                onPressed: () => showConfirmModal(context), // Al procesar el audio abre directamente el confirmador
                icon: const Icon(Icons.check, color: AppColors.darkGreen, size: 18),
                label: const Text(
                  'Procesar audio',
                  style: TextStyle(
                    color: AppColors.darkGreen,
                    fontWeight: FontWeight.bold,
                    fontSize: 13.5,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.lime,
                  elevation: 0,
                  shape: const StadiumBorder(),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: onManualRegister,
            child: const Text(
              'Registrar manualmente',
              style: TextStyle(
                color: AppColors.wine,
                fontSize: 12,
                fontWeight: FontWeight.bold,
                decoration: TextDecoration.underline,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTestChip(String label, {bool isSelected = false, VoidCallback? onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.wine : AppColors.cardCream,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? AppColors.wine : AppColors.wine.withOpacity(0.3),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? AppColors.cream : AppColors.wine,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

// =========================================================================
// 2. MODAL DE ERROR / NO ENTENDÍ
// =========================================================================
class VoiceErrorModal extends StatelessWidget {
  final VoidCallback onTryAgain;
  final VoidCallback onManualRegister;

  const VoiceErrorModal({
    super.key,
    required this.onTryAgain,
    required this.onManualRegister,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.mutedPink,
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withOpacity(0.6),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.error_outline, color: AppColors.wine, size: 18),
              ),
              const SizedBox(width: 8),
              const Text(
                'Error',
                style: TextStyle(
                  color: AppColors.wine,
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const Spacer(),
              InkWell(
                onTap: () => Navigator.pop(context),
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink.withOpacity(0.5),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.close, color: AppColors.wine, size: 18),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Chips superiores en el modal de error conectados
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildTestChip('a) No se escuchó', isSelected: true, onTap: null),
                const SizedBox(width: 8),
                _buildTestChip('Confirmado (Simular)', isSelected: false, onTap: () => showConfirmModal(context)),
              ],
            ),
          ),
          const SizedBox(height: 16),

          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.25),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: AppColors.wine.withOpacity(0.4),
                width: 1.5,
              ),
            ),
            child: Center(
              child: Container(
                width: 45,
                height: 45,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withOpacity(0.4),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.mic_off, color: AppColors.wine, size: 22),
              ),
            ),
          ),
          const SizedBox(height: 16),

          const Text(
            'No te alcancé a escuchar',
            style: TextStyle(
              color: AppColors.wine,
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 8),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              'Acércate al micrófono y mantén presionado mientras hablas.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.darkGreen,
                fontSize: 12,
                height: 1.3,
              ),
            ),
          ),
          const SizedBox(height: 16),

          _buildExampleChip(Icons.lightbulb_outline, '“\$14 mil en almuerzo”'),
          const SizedBox(height: 8),
          _buildExampleChip(Icons.directions_bus_outlined, '“\$3 mil en TransMilenio”'),
          const SizedBox(height: 20),

          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(30),
              border: const Border(bottom: BorderSide(color: AppColors.darkGreen, width: 3.5)),
            ),
            child: SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: onTryAgain,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.lime,
                  elevation: 0,
                  shape: const StadiumBorder(),
                ),
                child: const Text('Intentar de nuevo ↻', style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold)),
              ),
            ),
          ),
          const SizedBox(height: 10),
          TextButton(
            onPressed: onManualRegister,
            child: const Text(
              'Registrar manualmente',
              style: TextStyle(
                color: AppColors.wine,
                fontWeight: FontWeight.bold,
                fontSize: 12,
                decoration: TextDecoration.underline,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTestChip(String label, {bool isSelected = false, VoidCallback? onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.wine : AppColors.cardCream,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? AppColors.wine : AppColors.wine.withOpacity(0.3),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? AppColors.cream : AppColors.wine,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  Widget _buildExampleChip(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: AppColors.wine, size: 16),
          const SizedBox(width: 8),
          Text(
            text,
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

// =========================================================================
// 3. MODAL CONFIRMAR O EDITAR DATOS
// =========================================================================
class ConfirmDataModal extends StatefulWidget {
  const ConfirmDataModal({super.key});

  @override
  State<ConfirmDataModal> createState() => _ConfirmDataModalState();
}

class _ConfirmDataModalState extends State<ConfirmDataModal> {
  String selectedTab = 'Gasto';

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: const BoxDecoration(
                    color: AppColors.wine,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.check, color: AppColors.cream, size: 14),
                ),
                const SizedBox(width: 8),
                const Text(
                  '¿Lo entendí bien?',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const Spacer(),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close, color: AppColors.wine),
                ),
              ],
            ),
            const SizedBox(height: 12),

            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _buildTabChip('Gasto', '(-\$14.000)', true),
                  const SizedBox(width: 8),
                  _buildTabChip('Ingreso', '(+\$200.000)', false),
                  const SizedBox(width: 8),
                  _buildTabChip('Ahorro', '(\$250.000)', false),
                ],
              ),
            ),
            const SizedBox(height: 16),

            Container(
              padding: const EdgeInsets.all(18),
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
                      const Icon(Icons.trending_down, color: AppColors.wine, size: 24),
                      const SizedBox(width: 8),
                      const Text(
                        '-\$14.000',
                        style: TextStyle(
                          color: AppColors.wine,
                          fontSize: 24,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.mutedPink,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Text(
                          'Gasto',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  _buildEditableRow(Icons.restaurant, 'Categoría', 'Alimentación'),
                  const SizedBox(height: 10),
                  _buildEditableRow(Icons.account_balance_wallet, 'Medio de pago', 'Nequi', badge: 'Por defecto'),
                  const SizedBox(height: 10),
                  _buildEditableRow(Icons.label_outline, 'Concepto', 'Almuerzo corriente'),
                  const SizedBox(height: 10),
                  _buildEditableRow(Icons.access_time, 'Fecha y hora', 'Hoy, 12:40'),
                ],
              ),
            ),
            const SizedBox(height: 20),

            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(30),
                border: const Border(bottom: BorderSide(color: AppColors.darkGreen, width: 3.5)),
              ),
              child: SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('¡Registro guardado con éxito!')),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.lime,
                    elevation: 0,
                    shape: const StadiumBorder(),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Text(
                        'Guardar registro',
                        style: TextStyle(
                          color: AppColors.darkGreen,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      SizedBox(width: 6),
                      Icon(Icons.check, color: AppColors.darkGreen, size: 18),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
            Center(
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text(
                  'Descartar',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTabChip(String label, String amount, bool isSelected) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: isSelected ? AppColors.wine : AppColors.cardCream,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: isSelected ? AppColors.wine : AppColors.wine.withOpacity(0.2),
        ),
      ),
      child: Text(
        '$label $amount',
        style: TextStyle(
          color: isSelected ? AppColors.cream : AppColors.wine,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildEditableRow(IconData icon, String title, String value, {String? badge}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withOpacity(0.1)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.5),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: AppColors.wine, size: 16),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    Text(
                      value,
                      style: const TextStyle(
                        color: AppColors.wine,
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (badge != null) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.mutedPink.withOpacity(0.6),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          badge,
                          style: const TextStyle(
                            color: AppColors.wine,
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          const Icon(Icons.edit_outlined, color: AppColors.darkGreen, size: 18),
        ],
      ),
    );
  }
}

// =========================================================================
// 4. MODAL DE REGISTRO MANUAL DINÁMICO
// =========================================================================
class ManualRegisterModal extends StatefulWidget {
  final VoidCallback onBackToVoice;

  const ManualRegisterModal({super.key, required this.onBackToVoice});

  @override
  State<ManualRegisterModal> createState() => _ManualRegisterModalState();
}

class _ManualRegisterModalState extends State<ManualRegisterModal> {
  String selectedType = 'Ahorro';
  String selectedCategory = 'Viaje a Cartagena';
  String selectedPayment = 'Efectivo';
  String amountText = '14.000';

  final List<String> payments = ['Efectivo', 'Nequi', 'Daviplata', 'Tarjeta'];

  void _onCalcPress(String value) {
    setState(() {
      if (value == 'C') {
        amountText = '0';
      } else if (value == '⌫') {
        if (amountText.isNotEmpty && amountText != '0') {
          amountText = amountText.substring(0, amountText.length - 1);
          if (amountText.isEmpty) amountText = '0';
        }
      } else {
        if (amountText == '0') {
          amountText = value;
        } else {
          amountText += value;
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final currentCategories = globalCategoriesByType[selectedType] ?? globalCategoriesByType['Gasto']!;
    final isAhorro = selectedType == 'Ahorro';

    return Container(
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                const Text(
                  'Registrar Movimiento',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const Spacer(),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close, color: AppColors.wine),
                ),
              ],
            ),
            const SizedBox(height: 12),

            Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppColors.wine.withOpacity(0.3)),
              ),
              child: Row(
                children: ['Gasto', 'Ingreso', 'Ahorro'].map((type) {
                  final isSelected = selectedType == type;
                  return Expanded(
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          selectedType = type;
                          final list = globalCategoriesByType[type];
                          if (list != null && list.isNotEmpty) {
                            selectedCategory = list[0]['name'] as String;
                          }
                        });
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        decoration: BoxDecoration(
                          color: isSelected ? AppColors.wine : Colors.transparent,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          type,
                          style: TextStyle(
                            color: isSelected ? AppColors.cream : AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 16),

            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.wine.withOpacity(0.3)),
              ),
              child: Text(
                '\$ $amountText|',
                style: const TextStyle(
                  color: AppColors.wine,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(height: 12),

            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.wine.withOpacity(0.15)),
              ),
              child: Column(
                children: [
                  _buildCalcRow(['C', '%', '÷', '⌫']),
                  const SizedBox(height: 6),
                  _buildCalcRow(['7', '8', '9', '×']),
                  const SizedBox(height: 6),
                  _buildCalcRow(['4', '5', '6', '-']),
                  const SizedBox(height: 6),
                  _buildCalcRow(['1', '2', '3', '+']),
                  const SizedBox(height: 6),
                  _buildCalcRow(['00', '0', '000', '=']),
                ],
              ),
            ),
            const SizedBox(height: 16),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  isAhorro ? '¿A qué meta vas a aportar? *' : 'Categoría *',
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                const Text(
                  'Obligatorio',
                  style: TextStyle(color: AppColors.darkGreen, fontSize: 11),
                ),
              ],
            ),
            const SizedBox(height: 10),

            isAhorro
                ? ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: currentCategories.length,
              itemBuilder: (context, index) {
                final cat = currentCategories[index];
                final catName = cat['name'] as String;
                final isSelected = selectedCategory == catName;
                final isAdd = cat['isAdd'] == true;
                final subtitle = cat['subtitle'] as String? ?? '';

                if (isAdd || subtitle == 'Sin meta fija') {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8.0),
                    child: GestureDetector(
                      onTap: () => setState(() => selectedCategory = catName),
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: isSelected ? AppColors.lime : AppColors.cardCream,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: isSelected ? AppColors.darkGreen : AppColors.wine.withOpacity(0.2),
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(cat['icon'] as IconData, color: isSelected ? AppColors.darkGreen : AppColors.wine),
                            const SizedBox(width: 12),
                            Text(
                              catName,
                              style: TextStyle(
                                color: isSelected ? AppColors.darkGreen : AppColors.wine,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                            const Spacer(),
                            if (isSelected)
                              const Icon(Icons.check_circle, color: AppColors.darkGreen, size: 18),
                          ],
                        ),
                      ),
                    ),
                  );
                }

                final progress = (cat['progress'] as num?)?.toDouble() ?? 0.0;
                final current = cat['current'] as int? ?? 0;
                final total = cat['total'] as int? ?? 1;
                final tag = cat['tag'] as String?;

                return Padding(
                  padding: const EdgeInsets.only(bottom: 10.0),
                  child: GestureDetector(
                    onTap: () => setState(() => selectedCategory = catName),
                    child: Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: isSelected ? AppColors.lime.withOpacity(0.3) : AppColors.cardCream,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: isSelected ? AppColors.darkGreen : AppColors.wine.withOpacity(0.2),
                          width: isSelected ? 1.5 : 1,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: AppColors.mutedPink.withOpacity(0.4),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Icon(cat['icon'] as IconData, color: AppColors.wine, size: 20),
                              ),
                              const SizedBox(width: 12),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    catName,
                                    style: const TextStyle(
                                      color: AppColors.wine,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 13,
                                    ),
                                  ),
                                  Text(
                                    subtitle,
                                    style: const TextStyle(
                                      color: AppColors.darkGreen,
                                      fontSize: 11,
                                    ),
                                  ),
                                ],
                              ),
                              const Spacer(),
                              if (tag != null)
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: AppColors.lime,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    tag,
                                    style: const TextStyle(
                                      color: AppColors.darkGreen,
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              if (isSelected && tag == null)
                                const Icon(Icons.check_circle, color: AppColors.darkGreen, size: 20),
                            ],
                          ),
                          const SizedBox(height: 12),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(10),
                            child: LinearProgressIndicator(
                              value: progress,
                              backgroundColor: AppColors.mutedPink.withOpacity(0.3),
                              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.wine),
                              minHeight: 6,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                '\$$current de \$$total',
                                style: const TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.w600),
                              ),
                              Text(
                                '${(progress * 100).toInt()}%',
                                style: const TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            )
                : GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
                childAspectRatio: 1.1,
              ),
              itemCount: currentCategories.length,
              itemBuilder: (context, index) {
                final cat = currentCategories[index];
                final categoryName = cat['name'] as String;
                final isSelected = selectedCategory == categoryName;

                return GestureDetector(
                  onTap: () => setState(() => selectedCategory = categoryName),
                  child: Container(
                    decoration: BoxDecoration(
                      color: isSelected ? AppColors.lime : AppColors.cardCream,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isSelected ? AppColors.darkGreen : AppColors.wine.withOpacity(0.2),
                      ),
                    ),
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(cat['icon'] as IconData, color: isSelected ? AppColors.darkGreen : AppColors.wine, size: 24),
                          const SizedBox(height: 6),
                          Text(
                            categoryName,
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: isSelected ? AppColors.darkGreen : AppColors.wine,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),

            Text(
              isAhorro ? '¿De qué cuenta sale el dinero?' : (selectedType == 'Ingreso' ? '¿A qué cuenta entró?' : 'Medio de pago'),
              style: const TextStyle(
                color: AppColors.wine,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              children: payments.map((pay) {
                final isPaySelected = selectedPayment == pay;
                return ChoiceChip(
                  label: Text(pay),
                  selected: isPaySelected,
                  onSelected: (selected) {
                    setState(() => selectedPayment = pay);
                  },
                  selectedColor: AppColors.mutedPink,
                  backgroundColor: AppColors.cardCream,
                  labelStyle: const TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 14),

            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.wine.withOpacity(0.2)),
              ),
              child: Row(
                children: const [
                  Icon(Icons.edit_note, color: AppColors.wine, size: 18),
                  SizedBox(width: 8),
                  Text(
                    'Más detalles (opcional)',
                    style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                  Spacer(),
                  Icon(Icons.keyboard_arrow_down, color: AppColors.wine),
                ],
              ),
            ),
            const SizedBox(height: 20),

            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(30),
                border: const Border(bottom: BorderSide(color: AppColors.darkGreen, width: 3.5)),
              ),
              child: SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('¡Movimiento registrado con éxito!')),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.lime,
                    elevation: 0,
                    shape: const StadiumBorder(),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Text('Guardar registro', style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 14)),
                      SizedBox(width: 6),
                      Icon(Icons.arrow_forward, color: AppColors.darkGreen, size: 18),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
            Center(
              child: TextButton.icon(
                onPressed: widget.onBackToVoice,
                icon: const Icon(Icons.mic, color: AppColors.wine, size: 16),
                label: const Text(
                  'Mejor te hablo',
                  style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCalcRow(List<String> keys) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: keys.map((key) {
        final bool isEquals = key == '=';
        final bool isPinkButton = ['C', '%', '÷', '⌫', '×', '-', '+'].contains(key);

        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 3),
            child: ElevatedButton(
              onPressed: () => _onCalcPress(key),
              style: ElevatedButton.styleFrom(
                backgroundColor: isEquals
                    ? AppColors.lime
                    : (isPinkButton ? AppColors.mutedPink : AppColors.cardCream),
                foregroundColor: AppColors.wine,
                elevation: 0,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: AppColors.wine.withOpacity(0.15)),
                ),
              ),
              child: key == '⌫'
                  ? const Icon(Icons.backspace_outlined, size: 18, color: AppColors.wine)
                  : Text(
                key,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                  color: isEquals ? AppColors.darkGreen : AppColors.wine,
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}