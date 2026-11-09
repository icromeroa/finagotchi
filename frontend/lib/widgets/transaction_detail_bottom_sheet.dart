import 'package:flutter/material.dart';
import 'package:frontend/theme/app_colors.dart';

class TransactionDetailBottomSheet extends StatefulWidget {
  final String title;
  final String subtitle;
  final String amount;
  final IconData icon;
  final bool isIncome;

  const TransactionDetailBottomSheet({
    super.key,
    required this.title,
    required this.subtitle,
    required this.amount,
    required this.icon,
    required this.isIncome,
  });

  @override
  State<TransactionDetailBottomSheet> createState() => _TransactionDetailBottomSheetState();
}

class _TransactionDetailBottomSheetState extends State<TransactionDetailBottomSheet> {
  bool _isAnulado = false; // Estado para alternar entre detalle normal y anulado

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
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Pestaña superior decorativa
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
            const SizedBox(height: 12),

            // Cabecera: Título y botón cerrar
            Row(
              children: [
                Text(
                  _isAnulado ? 'Anulado' : 'Detalle Movimiento',
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontSize: 20,
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
            const SizedBox(height: 16),

            // Icono central en círculo rosado
            Container(
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(
                color: AppColors.mutedPink,
                shape: BoxShape.circle,
              ),
              child: Icon(_isAnulado ? Icons.delete_sweep_outlined : widget.icon, color: AppColors.wine, size: 32),
            ),
            const SizedBox(height: 10),

            // Monto principal (tachado si está anulado)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  widget.amount,
                  style: TextStyle(
                    color: _isAnulado ? AppColors.darkGreen.withValues(alpha: 0.6) : (widget.isIncome ? AppColors.darkGreen : AppColors.wine),
                    fontSize: 26,
                    fontWeight: FontWeight.w900,
                    decoration: _isAnulado ? TextDecoration.lineThrough : TextDecoration.none,
                  ),
                ),
                if (!_isAnulado) ...[
                  const SizedBox(width: 4),
                  Icon(
                    widget.isIncome ? Icons.south_west : Icons.north_east,
                    color: widget.isIncome ? AppColors.darkGreen : AppColors.wine,
                    size: 20,
                  ),
                ],
              ],
            ),
            const SizedBox(height: 4),

            // Subtítulo o Título
            Text(
              widget.title,
              style: TextStyle(
                color: _isAnulado ? AppColors.darkGreen.withValues(alpha: 0.6) : AppColors.darkGreen,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),

            // Badge condicional
            if (!_isAnulado)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    Icon(Icons.mic, color: AppColors.wine, size: 14),
                    SizedBox(width: 5),
                    Text(
                      'Registrado por voz',
                      style: TextStyle(
                        color: AppColors.wine,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 20),

            // Tarjeta interna con los detalles
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.cream,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.wine.withValues(alpha: 0.15)),
              ),
              child: Column(
                children: [
                  _buildDetailRow('Categoría', 'Familia y detalles', Icons.restaurant, AppColors.darkGreen),
                  const Divider(height: 20, color: AppColors.mutedPink),
                  _buildDetailRow('Cuenta / Medio', 'Efectivo', Icons.account_balance_wallet_outlined, AppColors.wine),
                  const Divider(height: 20, color: AppColors.mutedPink),
                  _buildDetailRow('Fecha y hora', 'Hoy, 4:05 p. m.', Icons.access_time, AppColors.darkGreen),
                  const Divider(height: 20, color: AppColors.mutedPink),
                  _buildDetailRow('Origen', 'Desde tu FinaGotchi', Icons.devices, AppColors.wine),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Aviso si está anulado
            if (_isAnulado) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.darkGreen.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.info_outline, color: AppColors.darkGreen, size: 20),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'No suma a tus balances ni a tus puntos.',
                        style: TextStyle(
                          color: AppColors.darkGreen,
                          fontSize: 11.5,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Botón principal: Editar o Restaurar
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
                onTap: () {
                  if (_isAnulado) {
                    Navigator.pop(context); // Acción de restaurar
                  } else {
                    setState(() {
                      _isAnulado = true; // Cambia a vista de anulado al editar/anular
                    });
                  }
                },
                borderRadius: BorderRadius.circular(26),
                child: Center(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (_isAnulado) ...[
                        const Icon(Icons.undo, color: AppColors.darkGreen, size: 18),
                        const SizedBox(width: 6),
                      ],
                      Text(
                        _isAnulado ? 'Restaurar' : 'Editar movimiento',
                        style: const TextStyle(
                          color: AppColors.darkGreen,
                          fontWeight: FontWeight.w900,
                          fontSize: 14.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Botón inferior: Anular registro (Solo si no está anulado)
            if (!_isAnulado)
              Center(
                child: GestureDetector(
                  onTap: () {
                    setState(() {
                      _isAnulado = true;
                    });
                  },
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: const [
                      Icon(Icons.delete_outline, color: AppColors.wine, size: 16),
                      SizedBox(width: 6),
                      Text(
                        'Anular registro',
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
    );
  }

  Widget _buildDetailRow(String label, String value, IconData icon, Color valueColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: AppColors.darkGreen,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
        Row(
          children: [
            Icon(icon, size: 14, color: valueColor),
            const SizedBox(width: 5),
            Text(
              value,
              style: TextStyle(
                color: valueColor,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ],
    );
  }
}