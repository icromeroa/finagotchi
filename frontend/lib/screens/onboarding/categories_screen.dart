import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/create_category_modal.dart';

class CategoriesScreen extends StatefulWidget {
  const CategoriesScreen({super.key});

  @override
  State<CategoriesScreen> createState() => _CategoriesScreenState();
}

class _CategoriesScreenState extends State<CategoriesScreen> {
  bool _isGastosSelected = true;

  // Listas de categorías sin corchetes angulares conflictivos
  final List _gastosCategories = [
    {'icon': Icons.block, 'title': 'Deuda 1', 'subtitle': '0 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.train, 'title': 'Transporte', 'subtitle': '18 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.restaurant, 'title': 'Alimentación', 'subtitle': '23 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.family_restroom, 'title': 'Familia y detalles', 'subtitle': '6 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.sports_esports, 'title': 'Ocio y gustos', 'subtitle': '9 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.home_outlined, 'title': 'Vivienda y fijos', 'subtitle': '2 movs', 'tagText': 'FIJO', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.health_and_safety_outlined, 'title': 'Salud y aseo', 'subtitle': '4 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.trending_up, 'title': 'Ahorro e inversión', 'subtitle': '3 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.subscriptions_outlined, 'title': 'Suscripciones', 'subtitle': '3 movs', 'tagText': 'FIJO', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.fitness_center, 'title': 'Gimnasio', 'subtitle': '4 movs', 'tagText': 'TUYA', 'tagColor': AppColors.lime, 'isDoubleBadge': true, 'textColor': AppColors.darkGreen},
    {'icon': Icons.account_balance, 'title': 'Finanzas', 'subtitle': '0 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.handshake_outlined, 'title': 'Préstamos', 'subtitle': '1 mov', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.more_horiz, 'title': 'Otros', 'subtitle': '5 movs', 'tagText': 'Predet.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
  ];

  final List _ingresosCategories = [
    {'icon': Icons.favorite_border, 'title': 'Apoyo familiar', 'subtitle': '2 movs', 'tagText': 'PREDET.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.work_outline, 'title': 'Trabajo', 'subtitle': '0 movs', 'tagText': 'PREDET.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.school_outlined, 'title': 'Beca', 'subtitle': '1 mov', 'tagText': 'PREDET.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.monetization_on_outlined, 'title': 'Otros ingresos', 'subtitle': '1 mov', 'tagText': 'PREDET.', 'tagColor': AppColors.mutedPink, 'textColor': AppColors.wine},
    {'icon': Icons.badge_outlined, 'title': 'Clases', 'subtitle': '2 movs', 'tagText': 'TUYA', 'tagColor': AppColors.lime, 'textColor': AppColors.darkGreen},
  ];

  @override
  Widget build(BuildContext context) {
    final currentCategories = _isGastosSelected ? _gastosCategories : _ingresosCategories;
    final totalMovs = _isGastosSelected ? '66 movimientos registrados' : '4 movimientos registrados';

    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // BARRA SUPERIOR
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  const Icon(Icons.grid_view_rounded, color: AppColors.wine, size: 22),
                  const SizedBox(width: 8),
                  const Text(
                    'Categorías',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 18,
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

            // PESTAÑAS
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              child: Container(
                height: 48,
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(24),
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
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.receipt_long_outlined,
                                color: _isGastosSelected ? AppColors.cardCream : AppColors.wine,
                                size: 16,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'Gastos',
                                style: TextStyle(
                                  color: _isGastosSelected ? AppColors.cardCream : AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
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
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.account_balance_wallet_outlined,
                                color: !_isGastosSelected ? AppColors.cardCream : AppColors.wine,
                                size: 16,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'Ingresos',
                                style: TextStyle(
                                  color: !_isGastosSelected ? AppColors.cardCream : AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
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
            ),

            // TARJETA NANCY
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 6, 16, 10),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withValues(alpha: 0.5),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.wine.withValues(alpha: 0.12)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: const BoxDecoration(
                        color: AppColors.cardCream,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.lightbulb_outline, color: AppColors.wine, size: 18),
                    ),
                    const SizedBox(width: 10),
                    const Expanded(
                      child: Text(
                        'Nancy aprende de estas categorías para ordenar tus audios y mensajes al instante.',
                        style: TextStyle(
                          color: AppColors.wine,
                          fontSize: 11.5,
                          height: 1.3,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // CABECERA CATÁLOGO
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'CATÁLOGO ACTIVO',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 11,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 0.5,
                    ),
                  ),
                  Text(
                    totalMovs,
                    style: const TextStyle(
                      color: AppColors.wine,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),

            // CUADRÍCULA DE CATEGORÍAS (DINÁMICA)
            Expanded(
              child: GridView.builder(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.35,
                ),
                itemCount: currentCategories.length + 1,
                itemBuilder: (context, index) {
                  if (index == currentCategories.length) {
                    return _buildCreateCard(context);
                  }

                  final cat = currentCategories[index];
                  return _buildCategoryCard(
                    icon: cat['icon'] as IconData,
                    title: cat['title'] as String,
                    subtitle: cat['subtitle'] as String,
                    tagText: cat['tagText'] as String,
                    tagColor: cat['tagColor'] as Color,
                    textColor: cat['textColor'] as Color,
                    isDoubleBadge: cat['isDoubleBadge'] as bool? ?? false,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoryCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required String tagText,
    required Color tagColor,
    required Color textColor,
    bool isDoubleBadge = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withValues(alpha: 0.6),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: AppColors.wine, size: 18),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: tagColor,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  tagText,
                  style: TextStyle(
                    color: textColor,
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          if (isDoubleBadge) ...[
            Align(
              alignment: Alignment.centerRight,
              child: Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Text(
                    'FIJO',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ),
          ],
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 12.5,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 1),
              Text(
                subtitle,
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCreateCard(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.lime.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.darkGreen.withValues(alpha: 0.2)),
      ),
      child: InkWell(
        onTap: () {
          showModalBottomSheet(
            context: context,
            isScrollControlled: true,
            backgroundColor: Colors.transparent,
            builder: (context) => Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(context).viewInsets.bottom,
              ),
              child: const CreateCategoryModal(),
            ),
          );
        },
        borderRadius: BorderRadius.circular(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                color: AppColors.darkGreen,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.add, color: AppColors.lime, size: 22),
            ),
            const SizedBox(height: 8),
            const Text(
              'Crear',
              style: TextStyle(
                color: AppColors.darkGreen,
                fontWeight: FontWeight.w900,
                fontSize: 13.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}