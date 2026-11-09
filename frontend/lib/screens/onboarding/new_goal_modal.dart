import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/finagotchi_dialogs.dart';

class NewGoalModal extends StatefulWidget {
  const NewGoalModal({super.key});

  @override
  State<NewGoalModal> createState() => _NewGoalModalState();
}

class _NewGoalModalState extends State<NewGoalModal> {
  // Controla las 4 vistas del flujo: 0 (Nueva meta base), 1 (Paso 1), 2 (Paso 2), 3 (Paso 3)
  int _currentStep = 0;

  // Índice del icono seleccionado en la cuadrícula de la vista base
  int _selectedIconIndex = 0;

  // Controla la frecuencia seleccionada en la vista base: 0 = Semanal, 1 = Quincenal, 2 = Mensual
  int _selectedFrequency = 1;

  // Switch de alerta física
  bool _physicalAlertEnabled = true;

  // Switch de sincronización con FinaGotchi Físico en el Paso 3
  bool _syncFingotchiEnabled = true;

  // Valor de la barra deslizante (Slider) en el Paso 1
  double _sliderValue = 0.65;

  // Índice del atajo rápido seleccionado en el Paso 1 (2 por defecto para '+1 año ✨')
  int _selectedShortcutIndex = 2;

  // Frecuencia de abono seleccionada en el Paso 2: 0 = Diario, 1 = Semanal, 2 = Mensual
  int _selectedFrequencyTab = 1;

  // Ritmo seleccionado en el Paso 2: 0 = Tranqui, 1 = Ideal Nancy, 2 = Acelerado
  int _selectedRythmIndex = 1;

  // Lista de iconos disponibles para la meta
  final List<IconData> _goalIcons = [
    Icons.flight_takeoff,
    Icons.phone_android,
    Icons.laptop,
    Icons.school,
    Icons.sports_esports,
    Icons.home,
    Icons.card_giftcard,
    Icons.directions_bike,
    Icons.coffee,
    Icons.pets,
    Icons.directions_car,
    Icons.fitness_center,
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.88,
      ),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ===================================================
          // ENCABEZADO DEL MODAL
          // ===================================================
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: AppColors.wine,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.tune, color: AppColors.cardCream, size: 18),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'Nueva meta',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
              GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.close, color: AppColors.wine, size: 18),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // ===================================================
          // CONTENIDO DINÁMICO SEGÚN LA VISTA ACTUAL
          // ===================================================
          Flexible(
            child: SingleChildScrollView(
              child: _currentStep == 0
                  ? _buildBaseViewContent()
                  : _currentStep == 1
                  ? _buildStep1Content()
                  : _currentStep == 2
                  ? _buildStep2Content()
                  : _buildStep3Content(),
            ),
          ),

          // ===================================================
          // BOTÓN INFERIOR DE ACCIÓN
          // ===================================================
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: () {
                setState(() {
                  if (_currentStep < 3) {
                    _currentStep++;
                  } else {
                    // 1. Cerramos el modal de creación de metas
                    Navigator.pop(context);

                    // 2. Mostramos el modal de éxito y configuramos el botón "Entendido"
                    FinaGotchiDialogs.showCreatedSuccess(
                      context,
                      onEntendido: () {
                        // AQUÍ: Se ejecuta al presionar "Entendido".
                        // Puedes redirigir a tu pantalla principal o de metas si lo requieres:
                        // Navigator.pushReplacementNamed(context, '/main');
                      },
                    );
                  }
                });
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.lime,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(25),
                ),
                side: BorderSide(color: AppColors.darkGreen.withOpacity(0.3), width: 1.5),
                elevation: 0,
              ),
              child: Text(
                _currentStep == 0
                    ? 'Paso 1'
                    : _currentStep == 1
                    ? 'Paso 2'
                    : _currentStep == 2
                    ? 'Paso 3'
                    : 'Crear meta',
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontWeight: FontWeight.w900,
                  fontSize: 15,
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Center(
            child: GestureDetector(
              onTap: () {
                if (_currentStep > 0) {
                  setState(() => _currentStep--);
                } else {
                  Navigator.pop(context);
                }
              },
              child: Text(
                _currentStep > 0 ? 'Regresar' : 'Descartar',
                style: const TextStyle(
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
    );
  }

  // ===================================================
  // WIDGET AUXILIAR PARA EL INDICADOR DE PASOS CON CÍRCULOS
  // ===================================================
  Widget _buildStepIndicator(int activeStep) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32.0),
            child: Row(
              children: [
                Expanded(
                  child: Stack(
                    children: [
                      Container(height: 3, color: AppColors.mutedPink),
                      FractionallySizedBox(
                        widthFactor: activeStep >= 2 ? 1.0 : 0.85,
                        child: Container(
                          height: 3,
                          color: activeStep >= 1 ? AppColors.darkGreen : AppColors.mutedPink,
                        ),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Container(
                    height: 3,
                    color: activeStep >= 3 ? AppColors.darkGreen : AppColors.mutedPink,
                  ),
                ),
              ],
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildStepNode(1, 'Plazo', activeStep >= 1),
              _buildStepNode(2, 'Cuota', activeStep >= 2),
              _buildStepNode(3, 'Plan Nancy', activeStep >= 3),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStepNode(int stepNumber, String label, bool isActive) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            color: isActive ? AppColors.darkGreen : AppColors.mutedPink,
            shape: BoxShape.circle,
          ),
          alignment: Alignment.center,
          child: Text(
            '$stepNumber',
            style: TextStyle(
              color: isActive ? AppColors.cardCream : AppColors.wine,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            color: isActive ? AppColors.darkGreen : AppColors.wine.withOpacity(0.6),
            fontSize: 10.5,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  // ===================================================
  // VISTA 1: NUEVA META (BASE)
  // ===================================================
  Widget _buildBaseViewContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text('Nombre de tu sueño', style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12)),
            Text('Requerido', style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.wine.withOpacity(0.2)),
          ),
          child: Row(
            children: const [
              Icon(Icons.card_travel, color: AppColors.wine, size: 18),
              SizedBox(width: 10),
              Expanded(
                child: Text('Viaje a Cartagena', style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 14)),
              ),
              Text('18/30', style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
            ],
          ),
        ),
        const SizedBox(height: 14),

        const Text('Monto total a alcanzar', style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12)),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.wine.withOpacity(0.2)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text('\$ 800.000', style: TextStyle(color: AppColors.darkGreen, fontSize: 20, fontWeight: FontWeight.w900)),
              Text('COP', style: TextStyle(color: AppColors.darkGreen, fontSize: 12, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        const SizedBox(height: 8),

        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _buildQuickAmountButton('+\$100.000'),
            _buildQuickAmountButton('+\$250.000'),
            _buildQuickAmountButton('+\$500.000'),
          ],
        ),
        const SizedBox(height: 14),

        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text('Elige un icono', style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12)),
            Text('Nancy lo celebrará al avanzar', style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 8),

        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _goalIcons.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 6,
              crossAxisSpacing: 8,
              mainAxisSpacing: 8,
            ),
            itemBuilder: (context, index) {
              final isSelected = _selectedIconIndex == index;
              return GestureDetector(
                onTap: () => setState(() => _selectedIconIndex = index),
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        color: isSelected ? AppColors.mutedPink : AppColors.cardCream,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: isSelected ? AppColors.wine : AppColors.wine.withOpacity(0.2),
                          width: isSelected ? 1.5 : 1,
                        ),
                      ),
                      alignment: Alignment.center,
                      child: Icon(_goalIcons[index], color: AppColors.wine, size: 18),
                    ),
                    if (isSelected)
                      Positioned(
                        top: -3,
                        right: -3,
                        child: Container(
                          width: 14,
                          height: 14,
                          decoration: const BoxDecoration(
                            color: AppColors.darkGreen,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.check, color: AppColors.cardCream, size: 10),
                        ),
                      ),
                  ],
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 16),

        const Text('Frecuencia de ahorro', style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 14)),
        const SizedBox(height: 10),

        Container(
          height: 44,
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Row(
            children: [
              _buildFreqTab('Semanal', 0),
              _buildFreqTab('Quincenal', 1),
              _buildFreqTab('Mensual', 2),
            ],
          ),
        ),
        const SizedBox(height: 12),

        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.savings, color: AppColors.wine, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text('Ahorra \$20.000 / semana', style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 12.5)),
                    SizedBox(height: 2),
                    Text('¡Alcanzarás tu meta el 15 Dic 2026! Recibirás avisos oportunos sin estresarte.', style: TextStyle(color: AppColors.wine, fontSize: 10, height: 1.2)),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.notifications_active, color: AppColors.wine, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text('Alerta en el Tamagotchi físico', style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 12.5)),
                    SizedBox(height: 2),
                    Text('Nancy parpadeará recordándote tu abono', style: TextStyle(color: AppColors.wine, fontSize: 10)),
                  ],
                ),
              ),
              Switch(
                value: _physicalAlertEnabled,
                activeColor: AppColors.lime,
                activeTrackColor: AppColors.darkGreen,
                onChanged: (val) => setState(() => _physicalAlertEnabled = val),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ===================================================
  // VISTA 2: NUEVA META PASO 1 (Plazo / Fecha límite)
  // ===================================================
  Widget _buildStep1Content() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text(
              'Paso 1 de 3',
              style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
            ),
            Row(
              children: [
                Icon(Icons.access_time, color: AppColors.darkGreen, size: 13),
                SizedBox(width: 4),
                Text(
                  '~1 min',
                  style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ],
            ),
          ],
        ),
        const SizedBox(height: 6),
        const Text(
          'Nancy calculará tu plan ideal paso a paso para no descuidar tu cupo diario.',
          style: TextStyle(color: AppColors.wine, fontSize: 11, height: 1.3),
        ),
        const SizedBox(height: 12),

        _buildStepIndicator(1),
        const SizedBox(height: 14),

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
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppColors.wine,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.flight_takeoff, color: AppColors.cardCream, size: 18),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Row(
                    children: [
                      Text('Viaje a Cartagena', style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
                      SizedBox(width: 6),
                      Text('META #1', style: TextStyle(color: AppColors.wine, fontSize: 9, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  SizedBox(height: 2),
                  Text('Objetivo: \$800.000 COP', style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold)),
                ],
              ),
              const Spacer(),
              const Icon(Icons.beach_access, color: AppColors.wine, size: 18),
            ],
          ),
        ),
        const SizedBox(height: 14),

        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: const [
                Icon(Icons.calendar_today, color: AppColors.darkGreen, size: 16),
                SizedBox(width: 6),
                Text(
                  '¿Para cuándo lo necesitas?',
                  style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
              decoration: BoxDecoration(
                color: AppColors.mutedPink,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                'Flexible',
                style: TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),

        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    'FECHA LÍMITE ELEGIDA',
                    style: TextStyle(color: AppColors.wine, fontSize: 9.5, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                  ),
                  SizedBox(height: 4),
                  Text(
                    '15 de\nDiciembre,\n2026',
                    style: TextStyle(color: AppColors.wine, fontSize: 22, fontWeight: FontWeight.w900, height: 1.1),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.darkGreen,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.calendar_today_outlined, color: AppColors.cardCream, size: 14),
                    SizedBox(width: 6),
                    Text(
                      'Editar',
                      style: TextStyle(color: AppColors.cardCream, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        const Text(
          'Atajos rápidos:',
          style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
        ),
        const SizedBox(height: 10),

        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(child: _buildShortcutButton('+3 meses', 0)),
            const SizedBox(width: 8),
            Expanded(child: _buildShortcutButton('+6 meses', 1)),
            const SizedBox(width: 8),
            Expanded(child: _buildShortcutButton('+1 año ✨', 2)),
          ],
        ),
        const SizedBox(height: 16),

        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Column(
            children: [
              SliderTheme(
                data: SliderThemeData(
                  activeTrackColor: AppColors.darkGreen,
                  inactiveTrackColor: AppColors.mutedPink,
                  thumbColor: AppColors.darkGreen,
                  overlayColor: AppColors.darkGreen.withOpacity(0.2),
                  trackHeight: 6,
                ),
                child: Slider(
                  value: _sliderValue,
                  onChanged: (val) => setState(() => _sliderValue = val),
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text('Corto (3m)', style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold)),
                    Text('Mediano (10m) •', style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold)),
                    Text('Largo (18m)', style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.lime.withOpacity(0.5),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.darkGreen.withOpacity(0.2)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.auto_awesome, color: AppColors.darkGreen, size: 18),
                      SizedBox(width: 8),
                      Text(
                        'Nancy calculando',
                        style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.darkGreen,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Text(
                      'ÓPTIMO',
                      style: TextStyle(color: AppColors.cardCream, fontSize: 9.5, fontWeight: FontWeight.w900),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              const Text(
                'Simulación en tiempo real',
                style: TextStyle(color: AppColors.darkGreen, fontSize: 10),
              ),
              const SizedBox(height: 10),
              const Text(
                'Faltan 42 semanas. Con este plazo tu cuota será de solo \$19.050/sem, manteniendo a salvo tus gastos diarios y tu Cupo Libre.',
                style: TextStyle(color: AppColors.darkGreen, fontSize: 11.5, height: 1.3, fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 10),
              const Icon(Icons.favorite_border, color: AppColors.darkGreen, size: 18),
            ],
          ),
        ),
      ],
    );
  }

  // ===================================================
  // VISTA 3: NUEVA META PASO 2 (Cuota / Frecuencia y Ritmos)
  // ===================================================
  Widget _buildStep2Content() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text(
              'Paso 2 de 3',
              style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
            ),
            Row(
              children: [
                Icon(Icons.access_time, color: AppColors.darkGreen, size: 13),
                SizedBox(width: 4),
                Text(
                  '~1 min',
                  style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ],
            ),
          ],
        ),
        const SizedBox(height: 6),
        const Text(
          'Nancy calculará tu plan ideal paso a paso para no descuidar tu cupo diario.',
          style: TextStyle(color: AppColors.wine, fontSize: 11, height: 1.3),
        ),
        const SizedBox(height: 12),

        _buildStepIndicator(2),
        const SizedBox(height: 14),

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
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppColors.wine,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.flight_takeoff, color: AppColors.cardCream, size: 18),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Row(
                    children: [
                      Text('Viaje a Cartagena', style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
                      SizedBox(width: 6),
                      Text('META #1', style: TextStyle(color: AppColors.wine, fontSize: 9, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  SizedBox(height: 2),
                  Text('Objetivo: \$800.000 COP', style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold)),
                ],
              ),
              const Spacer(),
              const Icon(Icons.umbrella, color: AppColors.wine, size: 18),
            ],
          ),
        ),
        const SizedBox(height: 16),

        const Text(
          'FRECUENCIA DE ABONO',
          style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 0.5),
        ),
        const SizedBox(height: 8),
        Container(
          height: 44,
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Row(
            children: [
              _buildFrequencyTab('Diario', 0),
              _buildFrequencyTab('Semanal', 1),
              _buildFrequencyTab('Mensual', 2),
            ],
          ),
        ),
        const SizedBox(height: 16),

        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text(
              'ELIGE TU RITMO',
              style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 0.5),
            ),
            Text(
              '⚡ Personalizable',
              style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 11),
            ),
          ],
        ),
        const SizedBox(height: 10),

        _buildRythmCard(
          index: 0,
          title: 'Ritmo Tranqui',
          badgeText: 'Flexible',
          amount: '\$10.000 / semana',
          description: 'Más holgura mensual. Tu meta tardará 38 semanas adicionales respecto a la fecha inicial.',
          isRecommended: false,
        ),
        const SizedBox(height: 12),

        _buildRythmCard(
          index: 1,
          title: 'Ritmo Ideal Nancy 🐾',
          badgeText: 'RECOMENDADO',
          amount: '\$20.000 / semana',
          description: 'Alcanzarás exactamente tu meta el 15 Dic 2026 sin tocar tu cupo de emergencias.',
          footerInfo: 'Calculado para tus ingresos promedio de los últimos 3 meses.',
          isRecommended: true,
        ),
        const SizedBox(height: 12),

        _buildRythmCard(
          index: 2,
          title: 'Modo Acelerado',
          badgeText: 'Meta Rápida ⚡',
          amount: '\$40.000 / semana',
          description: 'Completarías tu meta en tan solo 21 semanas, ahorrando 8 meses de espera.',
          isRecommended: false,
        ),
      ],
    );
  }

  // ===================================================
  // VISTA 4: NUEVA META PASO 3 (Plan Nancy / Resumen Final)
  // ===================================================
  Widget _buildStep3Content() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text(
              'Paso 3 de 3',
              style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
            ),
            Row(
              children: [
                Icon(Icons.access_time, color: AppColors.darkGreen, size: 13),
                SizedBox(width: 4),
                Text(
                  '~1 min',
                  style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ],
            ),
          ],
        ),
        const SizedBox(height: 6),
        const Text(
          'Todo listo! Revisa tu plan de vuelo antes de que Nancy empiece a engordar esta alcancía.',
          style: TextStyle(color: AppColors.wine, fontSize: 11, height: 1.3),
        ),
        const SizedBox(height: 12),

        _buildStepIndicator(3),
        const SizedBox(height: 14),

        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Column(
            children: [
              Row(
                children: [
                  Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      color: AppColors.wine,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.flight_takeoff, color: AppColors.cardCream, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text(
                        'Viaje a Cartagena',
                        style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 14),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'Meta recreativa & descanso',
                        style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.lime,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: const [
                        Icon(Icons.circle, size: 6, color: AppColors.darkGreen),
                        SizedBox(width: 4),
                        Text(
                          'Lista',
                          style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.w900),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              _buildDetailCard(
                icon: Icons.account_balance_wallet_outlined,
                title: 'Monto total',
                trailingWidget: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    Text(
                      '\$800.000',
                      style: TextStyle(color: AppColors.darkGreen, fontSize: 16, fontWeight: FontWeight.w900),
                    ),
                    SizedBox(width: 4),
                    Text(
                      'COP',
                      style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),

              _buildDetailCard(
                icon: Icons.calendar_view_week_outlined,
                title: 'Aporte semanal',
                trailingWidget: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: const [
                    Text(
                      '\$20.000 COP',
                      style: TextStyle(color: AppColors.wine, fontSize: 13.5, fontWeight: FontWeight.w900),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Cada lunes',
                      style: TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),

              _buildDetailCard(
                icon: Icons.calendar_today_outlined,
                title: 'Fecha límite',
                trailingWidget: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: const [
                    Text(
                      '15 Dic, 2026',
                      style: TextStyle(color: AppColors.wine, fontSize: 13.5, fontWeight: FontWeight.w900),
                    ),
                    SizedBox(height: 2),
                    Text(
                      '42 semanas de ruta',
                      style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),

              _buildDetailCard(
                icon: Icons.access_time_rounded,
                title: 'Primer abono',
                trailingWidget: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: const [
                    Text(
                      'Próximo lunes',
                      style: TextStyle(color: AppColors.wine, fontSize: 13.5, fontWeight: FontWeight.w900),
                    ),
                    SizedBox(height: 2),
                    Text(
                      '08:00 AM • Recordatorio',
                      style: TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // Tarjeta rosada "Nancy te anima"
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.mutedPink,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.wine.withOpacity(0.2)),
                ),
                alignment: Alignment.center,
                child: const Icon(Icons.pets, color: AppColors.wine, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'Nancy te anima',
                      style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 12),
                    ),
                    SizedBox(height: 4),
                    Text(
                      '“¡Qué chimba de plan! Con solo \$20.000 semanales tu bolsillo sigue blindado y yo me mantengo llenita y feliz. ¿Arrancamos ya?”',
                      style: TextStyle(color: AppColors.wine, fontSize: 11, height: 1.3, fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // Sincronizar con FinaGotchi Físico
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: AppColors.lime.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.memory, color: AppColors.darkGreen, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'Sincronizar con FinaGotchi Físico',
                      style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'ESP32 Bluetooth • Alertas en tu mesa',
                      style: TextStyle(color: AppColors.darkGreen, fontSize: 10),
                    ),
                  ],
                ),
              ),
              Switch(
                value: _syncFingotchiEnabled,
                activeColor: AppColors.cardCream,
                activeTrackColor: AppColors.darkGreen,
                onChanged: (val) => setState(() => _syncFingotchiEnabled = val),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // Sub-widget para cada fila de detalle estilo tarjeta en el Paso 3
  Widget _buildDetailCard({
    required IconData icon,
    required String title,
    required Widget trailingWidget,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.wine.withOpacity(0.1)),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.wine, size: 18),
          const SizedBox(width: 10),
          Text(
            title,
            style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12),
          ),
          const Spacer(),
          trailingWidget,
        ],
      ),
    );
  }

  Widget _buildQuickAmountButton(String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.wine.withOpacity(0.2)),
      ),
      child: Text(label, style: const TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildShortcutButton(String label, int index) {
    final isSelected = _selectedShortcutIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _selectedShortcutIndex = index),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? AppColors.wine : AppColors.cardCream,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.wine.withOpacity(isSelected ? 1.0 : 0.2)),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? AppColors.cardCream : AppColors.wine,
            fontSize: 11.5,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _buildFrequencyTab(String label, int index) {
    final isSelected = _selectedFrequencyTab == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _selectedFrequencyTab = index),
        child: Container(
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: isSelected ? AppColors.wine : Colors.transparent,
            borderRadius: BorderRadius.circular(18),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? AppColors.cardCream : AppColors.wine,
              fontWeight: FontWeight.bold,
              fontSize: 11.5,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRythmCard({
    required int index,
    required String title,
    required String badgeText,
    required String amount,
    required String description,
    String? footerInfo,
    required bool isRecommended,
  }) {
    final isSelected = _selectedRythmIndex == index;

    return GestureDetector(
      onTap: () => setState(() => _selectedRythmIndex = index),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.cardCream,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: isSelected ? AppColors.wine : AppColors.wine.withOpacity(0.2),
            width: isSelected ? 2.0 : 1.0,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Radio<int>(
                      value: index,
                      groupValue: _selectedRythmIndex,
                      activeColor: AppColors.wine,
                      onChanged: (val) => setState(() => _selectedRythmIndex = val!),
                    ),
                    Text(
                      title,
                      style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: isRecommended ? AppColors.mutedPink : AppColors.mutedPink.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    badgeText,
                    style: const TextStyle(color: AppColors.wine, fontSize: 9.5, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.only(left: 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    amount,
                    style: const TextStyle(color: AppColors.wine, fontSize: 16, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: const TextStyle(color: AppColors.darkGreen, fontSize: 10.5, height: 1.3),
                  ),
                  if (footerInfo != null) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.cream,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.wine.withOpacity(0.1)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.verified_outlined, color: AppColors.darkGreen, size: 14),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              footerInfo,
                              style: const TextStyle(color: AppColors.wine, fontSize: 9.5, fontWeight: FontWeight.w500),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFreqTab(String label, int index) {
    final isSel = _selectedFrequency == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _selectedFrequency = index),
        child: Container(
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: isSel ? AppColors.wine : Colors.transparent,
            borderRadius: BorderRadius.circular(18),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: isSel ? AppColors.cardCream : AppColors.wine,
              fontWeight: FontWeight.bold,
              fontSize: 11.5,
            ),
          ),
        ),
      ),
    );
  }
}