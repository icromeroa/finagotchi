import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

class ImproveMetricsWizardScreen extends StatefulWidget {
  final int initialStep; // Permite abrir directo cualquier sección seleccionada
  const ImproveMetricsWizardScreen({super.key, this.initialStep = 0});

  @override
  State<ImproveMetricsWizardScreen> createState() => _ImproveMetricsWizardScreenState();
}

class _ImproveMetricsWizardScreenState extends State<ImproveMetricsWizardScreen> {
  late final PageController _pageController;
  late int _currentStep;

  // Paso 1: Sobre ti
  double _edad = 22;
  String _generoSeleccionado = 'Hombre';
  String _ocupacionSeleccionada = 'Estudio y trabajo';
  String _nivelEducativo = 'Pregrado';
  String _viviendaSeleccionada = 'Con mi familia';

  // Paso 2: Ingresos
  bool _tieneIngresosPropios = true;
  String _frecuenciaIngreso = 'Quincenal';

  // Paso 3: Gastos y hábitos
  String _comprasImpulsivas = 'A veces';
  int _registrosSemana = 14;

  // Paso 4: Cuentas
  bool _usaAppPresupuesto = true;
  bool _anotaGastosManual = false;
  int _dificultadCuentas = 3;

  // Paso 5: Deudas y ahorro
  bool _tieneDeudaTarjeta = true;
  bool _pagaCuotas = true;
  bool _tieneFondoEmergencia = true;

  // Paso 6: Bienestar financiero
  double _nivelEstres = 4;
  bool _seSienteSeguro = true;

  @override
  void initState() {
    super.initState();
    _currentStep = widget.initialStep;
    _pageController = PageController(initialPage: widget.initialStep);
  }

  @override
  void didUpdateWidget(covariant ImproveMetricsWizardScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.initialStep != oldWidget.initialStep) {
      _currentStep = widget.initialStep;
      if (_pageController.hasClients) {
        _pageController.jumpToPage(widget.initialStep);
      }
    }
  }

  void _nextStep() {
    if (_currentStep < 5) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      Navigator.pop(context); // Al finalizar el último paso, regresa a la pantalla anterior
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cardCream, // Fondo claro general
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 8),
            // Píldora superior rosa decorativa
            Center(
              child: Container(
                width: 40,
                height: 5,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(2.5),
                ),
              ),
            ),
            const SizedBox(height: 8),

            // Contenido de las páginas del Wizard
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (index) {
                  setState(() {
                    _currentStep = index;
                  });
                },
                children: [
                  _buildStep1SobreTi(),
                  _buildStep2TusIngresos(),
                  _buildStep3GastosHabitos(),
                  _buildStep4ComoLlevasCuentas(),
                  _buildStep5DeudasAhorro(),
                  _buildStep6BienestarFinanciero(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ===================================================
  // CABECERA GENERAL REUTILIZABLE
  // ===================================================
  Widget _buildHeader(String title, IconData icon, String subtitle, int stepIndex, String progressText) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(icon, color: AppColors.wine, size: 22),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
            GestureDetector(
              onTap: () => Navigator.pop(context),
              child: Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withValues(alpha: 0.7),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.close, color: AppColors.wine, size: 20),
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(subtitle, style: const TextStyle(color: AppColors.darkGreen, fontSize: 12.5, fontWeight: FontWeight.w500)),
        const SizedBox(height: 12),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Paso ${stepIndex + 1} de 6', style: const TextStyle(color: AppColors.wine, fontSize: 12, fontWeight: FontWeight.bold)),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
              decoration: BoxDecoration(
                color: AppColors.mutedPink.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(progressText, style: const TextStyle(color: AppColors.wine, fontSize: 10.5, fontWeight: FontWeight.bold)),
            ),
          ],
        ),
        const SizedBox(height: 6),
        // Barritas de progreso fragmentadas
        Row(
          children: List.generate(6, (index) {
            bool isCompletedOrCurrent = index <= stepIndex;
            return Expanded(
              child: Container(
                height: 6,
                margin: EdgeInsets.only(right: index < 5 ? 4 : 0),
                decoration: BoxDecoration(
                  color: isCompletedOrCurrent ? AppColors.wine : AppColors.mutedPink.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
            );
          }),
        ),
        const SizedBox(height: 12),
      ],
    );
  }

  Widget _buildInfoBanner(String text) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.mutedPink.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.1)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: const BoxDecoration(color: AppColors.mutedPink, shape: BoxShape.circle),
            child: const Icon(Icons.location_pin, color: AppColors.wine, size: 16),
          ),
          const SizedBox(width: 10),
          Expanded(child: Text(text, style: const TextStyle(color: AppColors.wine, fontSize: 11.5, fontWeight: FontWeight.w500, height: 1.3))),
        ],
      ),
    );
  }

  // ===================================================
  // PASO 1: SOBRE TI
  // ===================================================
  Widget _buildStep1SobreTi() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader("Sobre ti", Icons.person_outline, "Conócete un poco más con Nancy", 0, "15% completado"),
          _buildInfoBanner("Con tu edad y ocupación, Nancy ajusta el tono y los consejos."),
          const SizedBox(height: 14),
          const Text("Edad", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.cream, // Fondo beige para elementos interactivos
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildPlusMinusButton(Icons.remove, () => setState(() => _edad = (_edad > 1 ? _edad - 1 : 1))),
                Text('${_edad.toInt()} años', style: const TextStyle(color: AppColors.darkGreen, fontSize: 16, fontWeight: FontWeight.w900)),
                _buildPlusMinusButton(Icons.add, () => setState(() => _edad++)),
              ],
            ),
          ),
          const SizedBox(height: 14),
          const Text("Género", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: ['Mujer', 'Hombre', 'No binario', 'Prefiero no decir'].map((gen) {
              final isSelected = _generoSeleccionado == gen;
              return ChoiceChip(
                label: Text(gen),
                selected: isSelected,
                onSelected: (_) => setState(() => _generoSeleccionado = gen),
                selectedColor: AppColors.lime,
                backgroundColor: AppColors.cream,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.darkGreen : AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(color: isSelected ? AppColors.darkGreen : AppColors.wine.withValues(alpha: 0.2)),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 14),
          const Text("Localidad de Bogotá", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.cream,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Row(
              children: const [
                Icon(Icons.location_on_outlined, color: AppColors.wine, size: 18),
                SizedBox(width: 8),
                Text('Chapinero', style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 13)),
                Spacer(),
                Icon(Icons.keyboard_arrow_down, color: AppColors.wine),
              ],
            ),
          ),
          const SizedBox(height: 14),
          const Text("Ocupación", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: ['Estudio', 'Estudio y trabajo', 'Trabajo', 'Otra'].map((ocu) {
              final isSelected = _ocupacionSeleccionada == ocu;
              return ChoiceChip(
                label: Text(ocu),
                selected: isSelected,
                onSelected: (_) => setState(() => _ocupacionSeleccionada = ocu),
                selectedColor: AppColors.lime,
                backgroundColor: AppColors.cream,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.darkGreen : AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(color: isSelected ? AppColors.darkGreen : AppColors.wine.withValues(alpha: 0.2)),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 14),
          const Text("Nivel educativo", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.cream,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Row(
              children: const [
                Icon(Icons.school_outlined, color: AppColors.wine, size: 18),
                SizedBox(width: 8),
                Text('Pregrado', style: TextStyle(color: AppColors.darkGreen, fontWeight: FontWeight.bold, fontSize: 13)),
                Spacer(),
                Icon(Icons.keyboard_arrow_down, color: AppColors.wine),
              ],
            ),
          ),
          const SizedBox(height: 14),
          const Text("Con quién vives", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: ['Con mi familia', 'Solo/a', 'Con compañeros', 'Otra'].map((viv) {
              final isSelected = _viviendaSeleccionada == viv;
              return ChoiceChip(
                label: Text(viv),
                selected: isSelected,
                onSelected: (_) => setState(() => _viviendaSeleccionada = viv),
                selectedColor: AppColors.lime,
                backgroundColor: AppColors.cream,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.darkGreen : AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(color: isSelected ? AppColors.darkGreen : AppColors.wine.withValues(alpha: 0.2)),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 24),
          _buildPrimaryButton("Guardar y continuar", _nextStep),
          const SizedBox(height: 8),
          _buildOmitirButton(),
        ],
      ),
    );
  }

  // ===================================================
  // PASO 2: TUS INGRESOS
  // ===================================================
  Widget _buildStep2TusIngresos() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader("Tus ingresos", Icons.account_balance_wallet_outlined, "Cuéntanos de dónde viene tu plata", 1, "30% completado"),
          _buildInfoBanner("Con tus ingresos calculo tu meta de registros y un presupuesto realista."),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text("¿Tienes ingresos propios?", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
                  Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                ],
              ),
              Switch(
                value: _tieneIngresosPropios,
                onChanged: (val) => setState(() => _tieneIngresosPropios = val),
                activeColor: AppColors.cream,
                activeTrackColor: AppColors.lime,
              ),
            ],
          ),
          const SizedBox(height: 10),
          _buildInputBox("Ingreso mensual por trabajo", "\$ 1.800.000", Icons.work_outline),
          const SizedBox(height: 12),
          _buildInputBox("Apoyo familiar mensual (Opcional)", "\$ 250.000", Icons.people_outline),
          const SizedBox(height: 12),
          _buildInputBox("Beca mensual (Opcional)", "\$ 0", Icons.school_outlined),
          const SizedBox(height: 12),
          _buildInputBox("Otros ingresos mensuales (Opcional)", "\$ 150.000", Icons.add_circle_outline),
          const SizedBox(height: 16),
          const Text("Frecuencia de ingreso", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: ['Semanal', 'Quincenal', 'Mensual', 'Irregular'].map((freq) {
              final isSelected = _frecuenciaIngreso == freq;
              return ChoiceChip(
                label: Text(freq),
                selected: isSelected,
                onSelected: (_) => setState(() => _frecuenciaIngreso = freq),
                selectedColor: AppColors.lime,
                backgroundColor: AppColors.cream,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.darkGreen : AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 11,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(color: isSelected ? AppColors.darkGreen : AppColors.wine.withValues(alpha: 0.2)),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.cream,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: const [
                Icon(Icons.lock_outline, color: AppColors.wine, size: 20),
                SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("Ingreso total mensual: \$ 2.200.000 COP", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 13)),
                      SizedBox(height: 2),
                      Text("• Calculado automáticamente", style: TextStyle(color: AppColors.darkGreen, fontSize: 11)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          _buildPrimaryButton("Guardar y continuar", _nextStep),
          const SizedBox(height: 8),
          _buildOmitirButton(),
        ],
      ),
    );
  }

  // ===================================================
  // PASO 3: TUS GASTOS Y HÁBITOS
  // ===================================================
  Widget _buildStep3GastosHabitos() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader("Tus gastos y hábitos", Icons.shopping_bag_outlined, "Aprende adónde va tu dinero sin estrés", 2, "45% completado"),
          _buildInfoBanner("Esto me ayuda a detectar tus gastos hormiga."),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text("Gasto total mensual aproximado", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
              Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
            ],
          ),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.cream,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Row(
              children: const [
                Icon(Icons.receipt_long_outlined, color: AppColors.wine, size: 18),
                SizedBox(width: 8),
                Text("\$ 1.300.000 COP", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 14)),
                Spacer(),
                Icon(Icons.edit_outlined, color: AppColors.darkGreen, size: 18),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text("Compras impulsivas", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
              Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: ['Casi nunca', 'A veces', 'Seguido', 'Siempre'].map((comp) {
              final isSelected = _comprasImpulsivas == comp;
              return ChoiceChip(
                label: Text(comp),
                selected: isSelected,
                onSelected: (_) => setState(() => _comprasImpulsivas = comp),
                selectedColor: AppColors.lime,
                backgroundColor: AppColors.cream,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.darkGreen : AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 11,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(color: isSelected ? AppColors.darkGreen : AppColors.wine.withValues(alpha: 0.2)),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 14),
          _buildCardCustomItem("Suscripciones", "Streaming, apps y servicios", "3 suscripciones", "\$ 65.000 COP"),
          const SizedBox(height: 10),
          _buildCardCustomItem("Domicilios al mes", "Comida rápida, delivery y antojos", "4 pedidos", "\$ 120.000 COP"),
          const SizedBox(height: 14),
          const Text("Registros que crees que harás por semana", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.cream,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildPlusMinusButton(Icons.remove, () => setState(() => _registrosSemana = (_registrosSemana > 1 ? _registrosSemana - 1 : 1))),
                Column(
                  children: [
                    Text('$_registrosSemana', style: const TextStyle(color: AppColors.wine, fontSize: 18, fontWeight: FontWeight.w900)),
                    const Text('registros/sem', style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                  ],
                ),
                _buildPlusMinusButton(Icons.add, () => setState(() => _registrosSemana++)),
              ],
            ),
          ),
          const SizedBox(height: 6),
          const Text("• Con esto personalizo tu meta de registros", style: TextStyle(color: AppColors.darkGreen, fontSize: 11)),
          const SizedBox(height: 20),
          _buildPrimaryButton("Guardar y continuar", _nextStep),
          const SizedBox(height: 8),
          _buildOmitirButton(),
        ],
      ),
    );
  }

  // ===================================================
  // PASO 4: CÓMO LLEVAS TUS CUENTAS
  // ===================================================
  Widget _buildStep4ComoLlevasCuentas() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader("Cómo llevas tus cuentas", Icons.menu_book_outlined, "Tus métodos actuales de control", 3, "60% completado"),
          _buildInfoBanner("Así entiendo qué te ha funcionado antes."),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text("¿Usas una app de presupuesto?", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
                  Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                ],
              ),
              Switch(
                value: _usaAppPresupuesto,
                onChanged: (val) => setState(() => _usaAppPresupuesto = val),
                activeColor: AppColors.cream,
                activeTrackColor: AppColors.lime,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text("¿Anotas tus gastos manualmente?", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
                  Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                ],
              ),
              Switch(
                value: _anotaGastosManual,
                onChanged: (val) => setState(() => _anotaGastosManual = val),
                activeColor: AppColors.cream,
                activeTrackColor: AppColors.lime,
              ),
            ],
          ),
          const SizedBox(height: 20),
          const Text("¿Qué tan difícil te resulta llevar tus cuentas?", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(5, (index) {
              final level = index + 1;
              final isSelected = _dificultadCuentas == level;
              return GestureDetector(
                onTap: () => setState(() => _dificultadCuentas = level),
                child: Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: isSelected ? AppColors.lime : AppColors.cream,
                    shape: BoxShape.circle,
                    border: Border.all(color: isSelected ? AppColors.darkGreen : AppColors.wine.withValues(alpha: 0.2), width: isSelected ? 2 : 1),
                  ),
                  child: Center(
                    child: Text(
                      '$level',
                      style: TextStyle(
                        color: isSelected ? AppColors.darkGreen : AppColors.wine,
                        fontWeight: FontWeight.w900,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
              );
            }),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text("Muy fácil", style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
              Text("Muy difícil", style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 40),
          _buildPrimaryButton("Guardar y continuar", _nextStep),
          const SizedBox(height: 8),
          _buildOmitirButton(),
        ],
      ),
    );
  }

  // ===================================================
  // PASO 5: DEUDAS Y AHORRO
  // ===================================================
  Widget _buildStep5DeudasAhorro() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader("Deudas y ahorro", Icons.savings_outlined, "Tu balance entre metas y compromisos", 4, "75% completado"),
          _buildInfoBanner("Con esto te propongo metas de ahorro posibles."),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text("¿Tienes deuda en tarjeta de crédito?", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
                  Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                ],
              ),
              Switch(
                value: _tieneDeudaTarjeta,
                onChanged: (val) => setState(() => _tieneDeudaTarjeta = val),
                activeColor: AppColors.cream,
                activeTrackColor: AppColors.lime,
              ),
            ],
          ),
          const SizedBox(height: 8),
          _buildInputBox("Saldo aproximado de la deuda", "\$ 850.000", Icons.credit_card_outlined),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text("¿Pagas compras a cuotas?", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
                  Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
                ],
              ),
              Switch(
                value: _pagaCuotas,
                onChanged: (val) => setState(() => _pagaCuotas = val),
                activeColor: AppColors.cream,
                activeTrackColor: AppColors.lime,
              ),
            ],
          ),
          const SizedBox(height: 14),
          _buildInputBox("Ahorro mensual aproximado (Opcional)", "\$ 200.000", Icons.savings_outlined),
          const SizedBox(height: 14),
          const Text("¿Tienes un fondo de emergencia? (Opcional)", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: ChoiceChip(
                  label: const Center(child: Text("Sí")),
                  selected: _tieneFondoEmergencia,
                  onSelected: (_) => setState(() => _tieneFondoEmergencia = true),
                  selectedColor: AppColors.lime,
                  backgroundColor: AppColors.cream,
                  labelStyle: TextStyle(color: _tieneFondoEmergencia ? AppColors.darkGreen : AppColors.wine, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ChoiceChip(
                  label: const Center(child: Text("No")),
                  selected: !_tieneFondoEmergencia,
                  onSelected: (_) => setState(() => _tieneFondoEmergencia = false),
                  selectedColor: AppColors.lime,
                  backgroundColor: AppColors.cream,
                  labelStyle: TextStyle(color: !_tieneFondoEmergencia ? AppColors.darkGreen : AppColors.wine, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _buildPrimaryButton("Guardar y continuar", _nextStep),
          const SizedBox(height: 8),
          _buildOmitirButton(),
        ],
      ),
    );
  }

  // ===================================================
  // PASO 6: BIENESTAR FINANCIERO
  // ===================================================
  Widget _buildStep6BienestarFinanciero() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader("Bienestar financiero", Icons.favorite_border, "Cómo te sientes respecto a tu dinero", 5, "100% completado"),
          _buildInfoBanner("Me ayuda a saber cómo acompañarte mejor."),
          const SizedBox(height: 20),
          const Text("¿Qué tan estresado/a te sientes por tu dinero?", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
          const SizedBox(height: 14),
          Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
              decoration: BoxDecoration(
                color: AppColors.mutedPink,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text('${_nivelEstres.toInt()}/10', style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 14)),
            ),
          ),
          Slider(
            value: _nivelEstres,
            min: 1,
            max: 10,
            divisions: 9,
            activeColor: AppColors.wine,
            inactiveColor: AppColors.mutedPink,
            onChanged: (val) => setState(() => _nivelEstres = val),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text("Tranquilo/a", style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
              Text("Muy estresado/a", style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 20),
          const Text("¿Te sientes seguro/a manejando tu plata?", style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
          const Text("(Opcional)", style: TextStyle(color: AppColors.darkGreen, fontSize: 10)),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: ChoiceChip(
                  label: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.check_circle_outline, size: 16),
                      SizedBox(width: 6),
                      Text("Sí"),
                    ],
                  ),
                  selected: _seSienteSeguro,
                  onSelected: (_) => setState(() => _seSienteSeguro = true),
                  selectedColor: AppColors.lime,
                  backgroundColor: AppColors.cream,
                  labelStyle: TextStyle(color: _seSienteSeguro ? AppColors.darkGreen : AppColors.wine, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ChoiceChip(
                  label: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.cancel_outlined, size: 16),
                      SizedBox(width: 6),
                      Text("No"),
                    ],
                  ),
                  selected: !_seSienteSeguro,
                  onSelected: (_) => setState(() => _seSienteSeguro = false),
                  selectedColor: AppColors.lime,
                  backgroundColor: AppColors.cream,
                  labelStyle: TextStyle(color: !_seSienteSeguro ? AppColors.darkGreen : AppColors.wine, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 30),
          _buildPrimaryButton("Finalizar", _nextStep),
          const SizedBox(height: 8),
          _buildOmitirButton(),
        ],
      ),
    );
  }

  // ===================================================
  // WIDGETS AUXILIARES DE APOYO
  // ===================================================
  Widget _buildPlusMinusButton(IconData icon, VoidCallback onPressed) {
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: AppColors.mutedPink.withValues(alpha: 0.3),
        shape: BoxShape.circle,
        border: Border.all(color: AppColors.darkGreen, width: 1.5),
      ),
      child: IconButton(
        padding: EdgeInsets.zero,
        icon: Icon(icon, size: 18, color: AppColors.darkGreen),
        onPressed: onPressed,
      ),
    );
  }

  Widget _buildInputBox(String label, String hint, IconData icon) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 12)),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.cream,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
          ),
          child: Row(
            children: [
              Icon(icon, color: AppColors.wine, size: 18),
              const SizedBox(width: 8),
              Text(hint, style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 13)),
              const Spacer(),
              const Text("COP", style: TextStyle(color: AppColors.darkGreen, fontSize: 11, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildCardCustomItem(String title, String subtitle, String badge, String value) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13)),
                Text(subtitle, style: const TextStyle(color: AppColors.darkGreen, fontSize: 11)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(value, style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 12)),
              Text(badge, style: const TextStyle(color: AppColors.darkGreen, fontSize: 10)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPrimaryButton(String text, VoidCallback onPressed) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.lime,
          foregroundColor: AppColors.darkGreen,
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
            side: const BorderSide(color: AppColors.darkGreen, width: 1.5),
          ),
          elevation: 0,
        ),
        onPressed: onPressed,
        child: Text(text, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14)),
      ),
    );
  }

  Widget _buildOmitirButton() {
    return Center(
      child: TextButton(
        onPressed: _nextStep,
        child: const Text("Omitir por ahora", style: TextStyle(color: AppColors.wine, fontSize: 12, fontWeight: FontWeight.bold)),
      ),
    );
  }
}