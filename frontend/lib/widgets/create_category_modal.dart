import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/finagotchi_dialogs.dart';

class CreateCategoryModal extends StatefulWidget {
  final bool isGastosInitial;

  const CreateCategoryModal({super.key, this.isGastosInitial = true});

  @override
  State<CreateCategoryModal> createState() => _CreateCategoryModalState();
}

class _CreateCategoryModalState extends State<CreateCategoryModal> {
  late bool _isGastosSelected;
  bool _discountFromFreeQuota = true;
  final TextEditingController _categoryNameController = TextEditingController(text: 'Clases');

  @override
  void initState() {
    super.initState();
    _isGastosSelected = widget.isGastosInitial;
  }

  // Íconos disponibles
  final List<IconData> _availableIcons = [
    Icons.fitness_center,
    Icons.pets,
    Icons.coffee_outlined,
    Icons.menu_book,
    Icons.sports_esports,
    Icons.headphones,
    Icons.shopping_bag_outlined,
    Icons.movie_outlined,
    Icons.local_florist_outlined,
    Icons.directions_bike,
    Icons.medication_outlined,
    Icons.laptop_mac,
  ];

  int _selectedIconIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.85,
      ),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
      ),
      child: Material(
        color: Colors.transparent,
        child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ===================================================
              // 1. BARRA SUPERIOR (Cerrar)
              // ===================================================
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
                      child: const Icon(Icons.close, color: AppColors.wine, size: 18),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 2),

              // ===================================================
              // 2. TÍTULO Y BADGE
              // ===================================================
              Row(
                children: [
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.wine.withValues(alpha: 0.2)),
                    ),
                    child: const Icon(Icons.check, color: AppColors.wine, size: 16),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'Nueva categoría',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // ===================================================
              // 3. PESTAÑAS: GASTOS / INGRESOS
              // ===================================================
              Container(
                height: 44,
                padding: const EdgeInsets.all(3),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: () => setState(() => _isGastosSelected = true),
                        child: Container(
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: _isGastosSelected ? AppColors.wine : Colors.transparent,
                            borderRadius: BorderRadius.circular(19),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.receipt_long_outlined,
                                color: _isGastosSelected ? AppColors.cardCream : AppColors.wine,
                                size: 15,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'Gastos',
                                style: TextStyle(
                                  color: _isGastosSelected ? AppColors.cardCream : AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12.5,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    Expanded(
                      child: GestureDetector(
                        onTap: () => setState(() => _isGastosSelected = false),
                        child: Container(
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: !_isGastosSelected ? AppColors.wine : Colors.transparent,
                            borderRadius: BorderRadius.circular(19),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.account_balance_wallet_outlined,
                                color: !_isGastosSelected ? AppColors.cardCream : AppColors.wine,
                                size: 15,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'Ingresos',
                                style: TextStyle(
                                  color: !_isGastosSelected ? AppColors.cardCream : AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12.5,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // ===================================================
              // 4. NOMBRE DE LA CATEGORÍA
              // ===================================================
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Nombre de la categoría',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 12.5,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.lime.withValues(alpha: 0.5),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Text(
                      'Requerido',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 9.5,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Container(
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
                ),
                child: TextField(
                  controller: _categoryNameController,
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 13.5,
                  ),
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.bookmark_border, color: AppColors.wine, size: 18),
                    suffixIcon: Icon(Icons.circle, color: AppColors.darkGreen, size: 10),
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: const [
                  Text(
                    'Ej: Clases particulares o beca',
                    style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5),
                  ),
                  Text(
                    '6/24',
                    style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              // ===================================================
              // 5. ELIGE UN ÍCONO
              // ===================================================
              Row(
                children: const [
                  Text(
                    'Elige un\nícono',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                      height: 1.1,
                    ),
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Nancy lo mostrará en tus movimientos',
                      style: TextStyle(color: AppColors.darkGreen, fontSize: 11),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.wine.withValues(alpha: 0.12)),
                ),
                child: GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 6,
                    mainAxisSpacing: 8,
                    crossAxisSpacing: 8,
                    childAspectRatio: 1,
                  ),
                  itemCount: _availableIcons.length,
                  itemBuilder: (context, index) {
                    final isSelected = _selectedIconIndex == index;
                    return GestureDetector(
                      onTap: () => setState(() => _selectedIconIndex = index),
                      child: Stack(
                        clipBehavior: Clip.none,
                        children: [
                          Container(
                            decoration: BoxDecoration(
                              color: isSelected ? AppColors.mutedPink : AppColors.cream,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: isSelected ? AppColors.wine : AppColors.wine.withValues(alpha: 0.15),
                                width: isSelected ? 1.5 : 1,
                              ),
                            ),
                            child: Center(
                              child: Icon(
                                _availableIcons[index],
                                color: AppColors.wine,
                                size: 20,
                              ),
                            ),
                          ),
                          if (isSelected)
                            Positioned(
                              top: -3,
                              right: -3,
                              child: Container(
                                width: 14,
                                height: 14,
                                decoration: BoxDecoration(
                                  color: AppColors.darkGreen,
                                  shape: BoxShape.circle,
                                  border: Border.all(color: AppColors.cardCream, width: 1.5),
                                ),
                                child: const Icon(Icons.check, color: AppColors.cardCream, size: 8),
                              ),
                            ),
                        ],
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 12),

              // ===================================================
              // 6. INTERRUPTOR DE CUPO LIBRE
              // ===================================================
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.wine.withValues(alpha: 0.12)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: AppColors.mutedPink,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.push_pin_outlined, color: AppColors.wine, size: 16),
                    ),
                    const SizedBox(width: 10),
                    const Expanded(
                      child: Text(
                        'Se descuenta de tu cupo libre cada mes',
                        style: TextStyle(
                          color: AppColors.wine,
                          fontWeight: FontWeight.bold,
                          fontSize: 11.5,
                        ),
                      ),
                    ),
                    Switch(
                      value: _discountFromFreeQuota,
                      activeColor: AppColors.darkGreen,
                      activeTrackColor: AppColors.lime,
                      inactiveThumbColor: AppColors.wine,
                      inactiveTrackColor: AppColors.mutedPink,
                      onChanged: (value) => setState(() => _discountFromFreeQuota = value),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // ===================================================
              // 7. PALABRAS QUE NANCY ENTENDERÁ
              // ===================================================
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.wine.withValues(alpha: 0.12)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: const [
                            Icon(Icons.mic_none, color: AppColors.wine, size: 16),
                            SizedBox(width: 6),
                            Text(
                              'Palabras que Nancy entenderá',
                              style: TextStyle(
                                color: AppColors.wine,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                        Row(
                          children: const [
                            Text(
                              '3 listas',
                              style: TextStyle(
                                color: AppColors.darkGreen,
                                fontWeight: FontWeight.bold,
                                fontSize: 11,
                              ),
                            ),
                            SizedBox(width: 2),
                            Icon(Icons.keyboard_arrow_up, color: AppColors.darkGreen, size: 16),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Si dices alguna de estas frases al auditar ingresos, Nancy la asignará de inmediato:',
                      style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5, height: 1.2),
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        _buildWordTag('"clases"'),
                        _buildWordTag('"honorarios"'),
                        _buildWordTag('"pago"'),
                        _buildAddTagButton(),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // ===================================================
              // 8. TARJETA NANCY: CONSEJO XP
              // ===================================================
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.darkGreen.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.darkGreen.withValues(alpha: 0.2)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: const BoxDecoration(
                        color: AppColors.darkGreen,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.pets, color: AppColors.cardCream, size: 18),
                    ),
                    const SizedBox(width: 10),
                    const Expanded(
                      child: Text(
                        'Nancy sonríe: Categorizar ingresos te da +15 XP de Cuidado en tu racha semanal.',
                        style: TextStyle(
                          color: AppColors.darkGreen,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          height: 1.25,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // ===================================================
              // 9. BOTÓN: OCULTAR CATEGORÍA
              // ===================================================
              SizedBox(
                width: double.infinity,
                height: 44,
                child: TextButton(
                  onPressed: () {
                    Navigator.pop(context);
                    FinaGotchiDialogs.showSaved(context);
                  },
                  style: TextButton.styleFrom(
                    backgroundColor: AppColors.cardCream,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: BorderSide(color: AppColors.wine.withValues(alpha: 0.12), width: 1),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.visibility_off_outlined, color: AppColors.darkGreen, size: 18),
                      SizedBox(width: 8),
                      Text(
                        'Ocultar categoría',
                        style: TextStyle(
                          color: AppColors.darkGreen,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 10),

              // ===================================================
              // 10. BOTÓN: ELIMINAR CATEGORÍA
              // ===================================================
              Center(
                child: GestureDetector(
                  onTap: () {
                    Navigator.pop(context);
                    FinaGotchiDialogs.showSaved(context);
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4.0),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: const [
                        Icon(Icons.delete_outline, color: AppColors.wine, size: 14),
                        SizedBox(width: 4),
                        Text(
                          'Eliminar categoría',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                            decoration: TextDecoration.underline,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // ===================================================
              // 11. BOTONES PRINCIPALES INFERIORES
              // ===================================================
              Container(
                height: 48,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: AppColors.lime,
                  borderRadius: BorderRadius.circular(24),
                  border: const Border(
                    bottom: BorderSide(color: AppColors.darkGreen, width: 3),
                  ),
                ),
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    FinaGotchiDialogs.showSaved(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.lime,
                    elevation: 0,
                    shadowColor: Colors.transparent,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(24),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Text(
                        'Actualizar categoría',
                        style: TextStyle(
                          color: AppColors.darkGreen,
                          fontWeight: FontWeight.w900,
                          fontSize: 14.5,
                        ),
                      ),
                      SizedBox(width: 6),
                      Icon(Icons.check, color: AppColors.darkGreen, size: 18),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Center(
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                  ),
                  child: const Text(
                    'Descartar',
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
    );
  }

  Widget _buildWordTag(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AppColors.mutedPink.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            text,
            style: const TextStyle(
              color: AppColors.wine,
              fontWeight: FontWeight.bold,
              fontSize: 11,
            ),
          ),
          const SizedBox(width: 6),
          const Icon(Icons.tag, color: AppColors.wine, size: 12),
        ],
      ),
    );
  }

  Widget _buildAddTagButton() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: AppColors.mutedPink,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
      ),
      child: const Text(
        '+ Añadir',
        style: TextStyle(
          color: AppColors.wine,
          fontWeight: FontWeight.bold,
          fontSize: 11,
        ),
      ),
    );
  }
}