
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../services/api_service.dart';
import '../../services/auth_session.dart';
import 'voice_recording_modal.dart';

// Mapa visual de categorías y metas
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
  ],
  'Ingreso': [
    {'name': 'Salario', 'icon': Icons.account_balance_wallet},
    {'name': 'Freelance', 'icon': Icons.card_travel},
    {'name': 'Beca', 'icon': Icons.school},
    {'name': 'Regalos', 'icon': Icons.card_giftcard},
    {'name': 'Inversión', 'icon': Icons.trending_up},
    {'name': 'Ventas', 'icon': Icons.store},
    {'name': 'Otros', 'icon': Icons.savings},
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

class ManualRegisterModal extends StatefulWidget {
  final VoidCallback onBackToVoice;
  final VoidCallback? onSaved;

  const ManualRegisterModal({
    super.key,
    required this.onBackToVoice,
    this.onSaved,
  });

  @override
  State<ManualRegisterModal> createState() =>
      _ManualRegisterModalState();
}

class _ManualRegisterModalState extends State<ManualRegisterModal> {
  final ApiService apiService = ApiService();

  String selectedType = 'Gasto';
  String selectedCategory = 'Alimentación';
  String selectedPayment = 'Efectivo';
  String amountText = '14.000';

  List<Map<String, dynamic>> backendCategories = [];

  bool isLoadingCategories = true;
  bool isSaving = false;
  String? categoryError;

  final List<String> payments = [
    'Efectivo',
    'Nequi',
    'Daviplata',
    'Tarjeta'
  ];

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  // ============================================================
  // CARGAR CATEGORÍAS DEL BACKEND
  // ============================================================

  Future<void> _loadCategories() async {
    final token = AuthSession.accessToken;

    if (token == null || token.isEmpty) {
      if (!mounted) return;

      setState(() {
        isLoadingCategories = false;
        categoryError = 'No hay una sesión iniciada.';
      });
      return;
    }

    try {
      final response = await apiService.getCategories(
        accessToken: token,
      );

      final data = response['data'];

      if (data is! List) {
        throw Exception(
          'El backend no devolvió una lista de categorías.',
        );
      }

      final loadedCategories = data
          .whereType<Map>()
          .map((category) => Map<String, dynamic>.from(category))
          .toList();

      if (!mounted) return;

      setState(() {
        backendCategories = loadedCategories;
        isLoadingCategories = false;
        categoryError = null;

        final available = _getCategoriesForType(selectedType);

        if (available.isNotEmpty) {
          selectedCategory =
              available.first['nombre'].toString();
        }
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isLoadingCategories = false;
        categoryError =
            e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  // ============================================================
  // OBTENER CATEGORÍAS SEGÚN EL TIPO
  // ============================================================

  List<Map<String, dynamic>> _getCategoriesForType(String type) {
    final backendType = type.toLowerCase();

    return backendCategories.where((category) {
      return category['tipo']?.toString().toLowerCase() ==
          backendType;
    }).toList();
  }

  // ============================================================
  // ICONOS VISUALES
  // ============================================================

  IconData _getCategoryIcon(String categoryName) {
    final visualCategories =
        globalCategoriesByType[selectedType] ?? [];

    for (final category in visualCategories) {
      if (category['name'] == categoryName) {
        return category['icon'] as IconData;
      }
    }

    return Icons.category;
  }

  // ============================================================
  // TECLADO NUMÉRICO
  // ============================================================

  void _onCalcPress(String value) {
    setState(() {
      if (value == 'C') {
        amountText = '0';
      } else if (value == '⌫') {
        if (amountText.isNotEmpty && amountText != '0') {
          amountText =
              amountText.substring(0, amountText.length - 1);

          if (amountText.isEmpty) {
            amountText = '0';
          }
        }
      } else if (RegExp(r'^\d+$').hasMatch(value)) {
        if (amountText == '0') {
          amountText = value;
        } else {
          amountText += value;
        }
      }
    });
  }

  int _getAmount() {
    final cleanAmount = amountText.replaceAll(
      RegExp(r'[^0-9]'),
      '',
    );

    return int.tryParse(cleanAmount) ?? 0;
  }

  // ============================================================
  // GUARDAR MOVIMIENTO EN EL BACKEND
  // ============================================================

  Future<void> _saveTransaction() async {
    if (isSaving) return;

    if (selectedType == 'Ahorro') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'La conexión de las metas de ahorro todavía está pendiente.',
          ),
        ),
      );
      return;
    }

    final token = AuthSession.accessToken;

    if (token == null || token.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Tu sesión ha expirado. Inicia sesión nuevamente.',
          ),
        ),
      );
      return;
    }

    final amount = _getAmount();

    if (amount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Ingresa un monto válido.'),
        ),
      );
      return;
    }

    if (isLoadingCategories) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Espera mientras cargan las categorías.',
          ),
        ),
      );
      return;
    }

    final matchingCategories =
    _getCategoriesForType(selectedType);

    final selectedCategoryData = matchingCategories.firstWhere(
          (category) =>
      category['nombre']?.toString() == selectedCategory,
      orElse: () => <String, dynamic>{},
    );

    if (selectedCategoryData.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Selecciona una categoría válida.'),
        ),
      );
      return;
    }

    final rawCategoryId = selectedCategoryData['id'] ??
        selectedCategoryData['categoria_id'];

    final categoryId = rawCategoryId is num
        ? rawCategoryId.toInt()
        : int.tryParse(rawCategoryId?.toString() ?? '');

    if (categoryId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'No se pudo identificar el ID de la categoría.',
          ),
        ),
      );
      return;
    }

    setState(() {
      isSaving = true;
    });

    try {
      await apiService.createTransaction(
        accessToken: token,
        tipo: selectedType.toLowerCase(),
        monto: amount,
        categoriaId: categoryId,
      );

      if (!mounted) return;

      final messenger = ScaffoldMessenger.of(context);

      Navigator.pop(context);

      widget.onSaved?.call();

      messenger.showSnackBar(
        const SnackBar(
          content: Text(
            '¡Movimiento registrado correctamente! 💗',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isSaving = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'No se pudo registrar el movimiento: $e',
          ),
          duration: const Duration(seconds: 5),
        ),
      );
    }
  }

  // ============================================================
  // INTERFAZ
  // ============================================================

  @override
  Widget build(BuildContext context) {
    final currentCategories =
        globalCategoriesByType[selectedType] ??
            globalCategoriesByType['Gasto']!;

    final availableCategories =
    _getCategoriesForType(selectedType);

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(32),
        ),
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
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    width: 30,
                    height: 30,
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink.withOpacity(0.5),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.close,
                      color: AppColors.wine,
                      size: 16,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // PESTAÑAS PRINCIPALES
            Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(
                  color: AppColors.wine.withOpacity(0.2),
                ),
              ),
              child: Row(
                children: ['Gasto', 'Ingreso', 'Ahorro'].map((type) {
                  final isSelected = selectedType == type;

                  return Expanded(
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          selectedType = type;

                          final available =
                          _getCategoriesForType(type);

                          if (available.isNotEmpty) {
                            selectedCategory =
                                available.first['nombre'].toString();
                          }
                        });
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          vertical: 10,
                        ),
                        decoration: BoxDecoration(
                          color: isSelected
                              ? AppColors.wine
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          type,
                          style: TextStyle(
                            color: isSelected
                                ? AppColors.cream
                                : AppColors.wine,
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

            // MONTO
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 14,
              ),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: AppColors.wine.withOpacity(0.2),
                ),
              ),
              child: Text(
                '\$ $amountText',
                style: const TextStyle(
                  color: AppColors.wine,
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
            const SizedBox(height: 12),

            // TECLADO
            _buildKeypadRow(['C', '%', '÷', '⌫']),
            const SizedBox(height: 6),
            _buildKeypadRow(['7', '8', '9', '×']),
            const SizedBox(height: 6),
            _buildKeypadRow(['4', '5', '6', '-']),
            const SizedBox(height: 6),
            _buildKeypadRow(['1', '2', '3', '+']),
            const SizedBox(height: 6),
            _buildKeypadRow(['00', '0', '000', '=']),
            const SizedBox(height: 20),

            // CATEGORÍA
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  selectedType == 'Ahorro'
                      ? '¿A qué meta vas a aportar? *'
                      : 'Categoría *',
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                const Text(
                  'Obligatorio',
                  style: TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            if (selectedType != 'Ahorro') ...[
              if (isLoadingCategories)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: CircularProgressIndicator(),
                  ),
                )
              else if (categoryError != null)
                Text(
                  'No se pudieron cargar las categorías: $categoryError',
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontSize: 12,
                  ),
                )
              else if (availableCategories.isEmpty)
                  const Text(
                    'No hay categorías disponibles para este tipo de movimiento.',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 12,
                    ),
                  )
                else
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate:
                    const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                      childAspectRatio: 1.35,
                    ),
                    itemCount: availableCategories.length,
                    itemBuilder: (context, index) {
                      final category = availableCategories[index];
                      final name = category['nombre'].toString();
                      final isSelected = selectedCategory == name;

                      return GestureDetector(
                        onTap: () {
                          setState(() {
                            selectedCategory = name;
                          });
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            vertical: 8,
                            horizontal: 4,
                          ),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? AppColors.lime.withOpacity(0.5)
                                : AppColors.cardCream,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: isSelected
                                  ? AppColors.darkGreen
                                  : AppColors.wine.withOpacity(0.15),
                              width: isSelected ? 1.5 : 1,
                            ),
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                _getCategoryIcon(name),
                                color: isSelected
                                    ? AppColors.darkGreen
                                    : AppColors.wine,
                                size: 20,
                              ),
                              const SizedBox(height: 6),
                              Text(
                                name,
                                textAlign: TextAlign.center,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  color: isSelected
                                      ? AppColors.darkGreen
                                      : AppColors.wine,
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
            ] else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: currentCategories.length,
                separatorBuilder: (_, __) =>
                const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final meta = currentCategories[index];
                  final isSelected =
                      selectedCategory == meta['name'];
                  final isAdd = meta['isAdd'] == true;

                  if (isAdd) {
                    return Container(
                      padding: const EdgeInsets.symmetric(
                        vertical: 14,
                        horizontal: 16,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: AppColors.wine.withOpacity(0.15),
                        ),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.add_circle_outline,
                            color: AppColors.wine,
                            size: 18,
                          ),
                          SizedBox(width: 8),
                          Text(
                            'Nueva meta',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    );
                  }

                  return Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? AppColors.lime.withOpacity(0.3)
                          : AppColors.cardCream,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isSelected
                            ? AppColors.darkGreen
                            : AppColors.wine.withOpacity(0.15),
                        width: isSelected ? 1.5 : 1,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          meta['icon'] as IconData,
                          color: AppColors.wine,
                          size: 20,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            meta['name'],
                            style: const TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 12.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),

            const SizedBox(height: 20),

            // MEDIO DE PAGO (VISUAL POR AHORA)
            Text(
              selectedType == 'Ahorro'
                  ? '¿De qué cuenta sale el dinero?'
                  : 'Medio de pago',
              style: const TextStyle(
                color: AppColors.wine,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
            const SizedBox(height: 10),

            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: payments.map((payment) {
                  final isSelected = selectedPayment == payment;

                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          selectedPayment = payment;
                        });
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: isSelected
                              ? AppColors.mutedPink
                              : AppColors.cardCream,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: isSelected
                                ? AppColors.wine
                                : AppColors.wine.withOpacity(0.2),
                          ),
                        ),
                        child: Row(
                          children: [
                            Text(
                              payment,
                              style: const TextStyle(
                                color: AppColors.wine,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                            if (isSelected) ...[
                              const SizedBox(width: 4),
                              const Icon(
                                Icons.check,
                                color: AppColors.wine,
                                size: 14,
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 16),

            // MÁS DETALLES
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 14,
                vertical: 12,
              ),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: AppColors.wine.withOpacity(0.15),
                ),
              ),
              child: const Row(
                children: [
                  Icon(
                    Icons.tune,
                    color: AppColors.wine,
                    size: 16,
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Más detalles (opcional)',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Spacer(),
                  Icon(
                    Icons.keyboard_arrow_down,
                    color: AppColors.wine,
                    size: 18,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // GUARDAR REGISTRO
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(30),
                border: const Border(
                  bottom: BorderSide(
                    color: AppColors.darkGreen,
                    width: 3.5,
                  ),
                ),
              ),
              child: SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: isSaving ? null : _saveTransaction,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.lime,
                    disabledBackgroundColor:
                    AppColors.lime.withOpacity(0.5),
                    elevation: 0,
                    shape: const StadiumBorder(),
                  ),
                  child: isSaving
                      ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: AppColors.darkGreen,
                    ),
                  )
                      : const Text(
                    'Guardar registro →',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),

            Center(
              child: TextButton.icon(
                onPressed: widget.onBackToVoice,
                icon: const Icon(
                  Icons.mic,
                  color: AppColors.wine,
                  size: 16,
                ),
                label: const Text(
                  'Mejor te hablo',
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

  // ============================================================
  // FILAS DEL TECLADO
  // ============================================================

  Widget _buildKeypadRow(List<String> keys) {
    return Row(
      children: keys.map((key) {
        final isSpecial = [
          'C',
          '%',
          '÷',
          '⌫',
          '×',
          '-',
          '+',
          '='
        ].contains(key);

        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 3),
            child: SizedBox(
              height: 40,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: isSpecial
                      ? AppColors.mutedPink.withOpacity(0.5)
                      : AppColors.cardCream,
                  foregroundColor: AppColors.wine,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: EdgeInsets.zero,
                ),
                onPressed: () => _onCalcPress(key),
                child: Text(
                  key,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: key == '='
                        ? AppColors.darkGreen
                        : AppColors.wine,
                  ),
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
