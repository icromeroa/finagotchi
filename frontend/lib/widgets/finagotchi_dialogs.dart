import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class FinaGotchiDialogs {
  // ===================================================
  // 1. MODAL: CREADO CON ÉXITO
  // ===================================================
  static void showCreatedSuccess(BuildContext context, {VoidCallback? onEntendido}) {
    _showCustomDialog(
      context: context,
      icon: Icons.add,
      iconBackgroundColor: AppColors.lime,
      title: 'Se ha creado con éxito',
      subtitle: 'Ya puedes usarla en tu app.',
      confirmText: 'Entendido',
      onConfirm: () {
        if (onEntendido != null) onEntendido();
      },
    );
  }

  // ===================================================
  // 2. MODAL: GUARDADO (Soporta showSaved y showSavedSuccess)
  // ===================================================
  static void showSaved(BuildContext context, {VoidCallback? onEntendido}) {
    _showCustomDialog(
      context: context,
      icon: Icons.bookmark_outline,
      iconBackgroundColor: AppColors.lime,
      title: 'Se ha guardado con éxito',
      subtitle: 'Tus cambios quedaron listos.',
      confirmText: 'Entendido',
      onConfirm: () {
        if (onEntendido != null) onEntendido();
      },
    );
  }

  static void showSavedSuccess(BuildContext context, {VoidCallback? onEntendido}) {
    showSaved(context, onEntendido: onEntendido);
  }

  // ===================================================
  // 3. MODAL: ACTUALIZADO
  // ===================================================
  static void showUpdated(BuildContext context, {VoidCallback? onEntendido}) {
    _showCustomDialog(
      context: context,
      icon: Icons.refresh_rounded,
      iconBackgroundColor: AppColors.lime,
      title: 'Se ha actualizado con éxito',
      subtitle: 'Ya ves la información al día.',
      confirmText: 'Entendido',
      onConfirm: () {
        if (onEntendido != null) onEntendido();
      },
    );
  }

  // ===================================================
  // 4. MODAL: ELIMINADO
  // ===================================================
  static void showDeleted(BuildContext context, {VoidCallback? onEntendido}) {
    _showCustomDialog(
      context: context,
      icon: Icons.delete_outline_rounded,
      iconBackgroundColor: AppColors.mutedPink,
      title: 'Se ha eliminado con éxito',
      subtitle: 'Ya no aparece en tu lista.',
      confirmText: 'Entendido',
      onConfirm: () {
        if (onEntendido != null) onEntendido();
      },
    );
  }

  // ===================================================
  // 5. MODAL: OCULTAR (Cancelar y Sí, ocultar)
  // ===================================================
  static void showHideConfirmation(BuildContext context, {VoidCallback? onConfirmHide}) {
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black.withOpacity(0.4),
      builder: (BuildContext dialogContext) {
        return Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(28),
            side: BorderSide(color: AppColors.darkGreen, width: 2),
          ),
          backgroundColor: AppColors.cream,
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink,
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.darkGreen, width: 1.5),
                  ),
                  child: const Icon(Icons.visibility_off_outlined, color: AppColors.wine, size: 24),
                ),
                const SizedBox(height: 16),
                const Text(
                  '¿Ocultar?',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'No aparecerá al registrar, pero tus movimientos se conservan. Puedes mostrarla cuando quieras.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 12,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 24),
                Row(
                  children: [
                    Expanded(
                      child: TextButton(
                        onPressed: () => Navigator.of(dialogContext).pop(),
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                        child: const Text(
                          'Cancelar',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Container(
                        height: 44,
                        decoration: BoxDecoration(
                          color: AppColors.darkGreen,
                          borderRadius: BorderRadius.circular(22),
                        ),
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.of(dialogContext).pop();
                            if (onConfirmHide != null) onConfirmHide();
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.lime,
                            elevation: 0,
                            shadowColor: Colors.transparent,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(22),
                              side: BorderSide(color: AppColors.darkGreen, width: 1.5),
                            ),
                          ),
                          child: const Text(
                            'Sí, ocultar',
                            style: TextStyle(
                              color: AppColors.darkGreen,
                              fontWeight: FontWeight.w900,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ===================================================
  // MÉTODO AUXILIAR PRIVADO PARA LOS MODALES DE UN BOTÓN
  // ===================================================
  static void _showCustomDialog({
    required BuildContext context,
    required IconData icon,
    required Color iconBackgroundColor,
    required String title,
    required String subtitle,
    required String confirmText,
    required VoidCallback onConfirm,
  }) {
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black.withOpacity(0.4),
      builder: (BuildContext dialogContext) {
        return Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(28),
            side: BorderSide(color: AppColors.darkGreen, width: 2),
          ),
          backgroundColor: AppColors.cream,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 28, 24, 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Stack(
                  clipBehavior: Clip.none,
                  alignment: Alignment.center,
                  children: [
                    Container(
                      width: 72,
                      height: 72,
                      decoration: BoxDecoration(
                        color: iconBackgroundColor,
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.darkGreen, width: 1.5),
                      ),
                      child: Icon(icon, color: AppColors.darkGreen, size: 38),
                    ),
                    Positioned(
                      bottom: -2,
                      right: -4,
                      child: Container(
                        width: 26,
                        height: 26,
                        decoration: BoxDecoration(
                          color: AppColors.lime,
                          shape: BoxShape.circle,
                          border: Border.all(color: AppColors.darkGreen, width: 1.5),
                        ),
                        child: const Icon(Icons.check, color: AppColors.darkGreen, size: 16),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Text(
                  title,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  subtitle,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 28),
                Container(
                  width: double.infinity,
                  height: 50,
                  decoration: BoxDecoration(
                    color: AppColors.darkGreen,
                    borderRadius: BorderRadius.circular(25),
                  ),
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.of(dialogContext).pop();
                      onConfirm();
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.lime,
                      elevation: 0,
                      shadowColor: Colors.transparent,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(25),
                        side: BorderSide(color: AppColors.darkGreen, width: 1.5),
                      ),
                    ),
                    child: Text(
                      confirmText,
                      style: const TextStyle(
                        color: AppColors.darkGreen,
                        fontWeight: FontWeight.w900,
                        fontSize: 15,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}