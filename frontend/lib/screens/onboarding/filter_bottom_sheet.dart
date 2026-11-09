import 'package:flutter/material.dart';
import 'package:frontend/theme/app_colors.dart';

class FilterBottomSheet extends StatefulWidget {
  const FilterBottomSheet({super.key});

  @override
  State<FilterBottomSheet> createState() => _FilterBottomSheetState();
}

class _FilterBottomSheetState extends State<FilterBottomSheet> {
  String _selectedPeriodo = 'Este mes';
  String _selectedMovimiento = 'Todos';
  final List<String> _categoriasSeleccionadas = ['Alimentación', 'Transporte'];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Pestaña superior decorativa rosa
            Center(
              child: Container(
                width: 44,
                height: 5,
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(2.5),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Cabecera: Icono filtros, título y botón cerrar
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: const BoxDecoration(
                    color: AppColors.wine,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.tune, color: AppColors.cardCream, size: 20),
                ),
                const SizedBox(width: 10),
                const Text(
                  'Filtros',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontSize: 22,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const Spacer(),
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    width: 36,
                    height: 36,
                    decoration: const BoxDecoration(
                      color: AppColors.mutedPink,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.close, color: AppColors.wine, size: 18),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Sección: Periodo
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Periodo',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.w900,
                    fontSize: 14,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink.withValues(alpha: 0.5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'Octubre 2026',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Opciones de Periodo
            Row(
              children: [
                _buildPeriodoChip('Este mes', true),
                const SizedBox(width: 8),
                _buildPeriodoChip('Mes pasado', false),
                const SizedBox(width: 8),
                _buildPeriodoChip('Últimos 30 días', false),
              ],
            ),
            const SizedBox(height: 12),

            // Fechas Desde / Hasta
            Row(
              children: [
                Expanded(child: _buildDateBox(Icons.calendar_today_outlined, 'Desde: 01/10/2026')),
                const SizedBox(width: 10),
                Expanded(child: _buildDateBox(Icons.calendar_today_outlined, 'Hasta: 24/10/2026')),
              ],
            ),
            const SizedBox(height: 20),

            // Sección: Tipo de movimiento
            const Text(
              'Tipo de movimiento',
              style: TextStyle(
                color: AppColors.wine,
                fontWeight: FontWeight.w900,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: AppColors.cream,
                borderRadius: BorderRadius.circular(26),
                border: Border.all(color: AppColors.wine.withValues(alpha: 0.2)),
              ),
              child: Row(
                children: ['Todos', 'Gastos', 'Ingresos'].map((tipo) {
                  bool isSelected = _selectedMovimiento == tipo;
                  return Expanded(
                    child: GestureDetector(
                      onTap: () => setState(() => _selectedMovimiento = tipo),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        decoration: BoxDecoration(
                          color: isSelected ? AppColors.wine : Colors.transparent,
                          borderRadius: BorderRadius.circular(22),
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          tipo,
                          style: TextStyle(
                            color: isSelected ? AppColors.cardCream : AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 12.5,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 20),

            // Sección: Categoría
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Categoría',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.w900,
                    fontSize: 14,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.lime,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.darkGreen.withValues(alpha: 0.3)),
                  ),
                  child: const Text(
                    '2 seleccionadas',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Chips de Categorías (Exactos a la imagen)
            Wrap(
              spacing: 8,
              runSpacing: 10,
              children: [
                _buildCategoryChip('🍽️ Alimentación', true),
                _buildCategoryChip('🚌 Transporte', true),
                _buildCategoryChip('🎁 Familia y detalles', false),
                _buildCategoryChip('🎉 Ocio y gustos', false),
                _buildCategoryChip('🏠 Vivienda', false),
                _buildCategoryChip('🍿 Suscripciones', false),
              ],
            ),
            const SizedBox(height: 28),

            // Botón principal: Aplicar filtros
            Container(
              height: 52,
              width: double.infinity,
              decoration: BoxDecoration(
                color: AppColors.lime,
                borderRadius: BorderRadius.circular(26),
                border: const Border(
                  bottom: BorderSide(color: AppColors.darkGreen, width: 3.5),
                ),
              ),
              child: InkWell(
                onTap: () => Navigator.pop(context),
                borderRadius: BorderRadius.circular(26),
                child: const Center(
                  child: Text(
                    'Aplicar filtros (23 resultados)',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontWeight: FontWeight.w900,
                      fontSize: 14.5,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Botón inferior: Limpiar todo
            Center(
              child: GestureDetector(
                onTap: () {},
                child: const Text(
                  'Limpiar todo',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
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

  Widget _buildPeriodoChip(String text, bool isSelected) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.wine : AppColors.cream,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppColors.wine.withValues(alpha: 0.25)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (isSelected) ...[
              Container(
                width: 16,
                height: 16,
                decoration: const BoxDecoration(
                  color: AppColors.cardCream,
                  shape: BoxShape.circle,
                ),
                child: const Center(
                  child: Icon(Icons.check, size: 11, color: AppColors.wine),
                ),
              ),
              const SizedBox(width: 5),
            ],
            Flexible(
              child: Text(
                text,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: isSelected ? AppColors.cardCream : AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 11.5,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDateBox(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.wine.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.wine, size: 16),
          const SizedBox(width: 8),
          Text(
            text,
            style: const TextStyle(
              color: AppColors.wine,
              fontSize: 11.5,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryChip(String label, bool isSelected) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
      decoration: BoxDecoration(
        color: isSelected ? AppColors.mutedPink : AppColors.cream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isSelected ? AppColors.wine : AppColors.wine.withValues(alpha: 0.2),
          width: isSelected ? 1.5 : 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: AppColors.wine,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
          if (isSelected) ...[
            const SizedBox(width: 6),
            const Icon(Icons.check, size: 14, color: AppColors.wine),
          ],
        ],
      ),
    );
  }
}