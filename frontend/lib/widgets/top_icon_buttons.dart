import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

// 1. Botón circular base
class CircleIconButton extends StatelessWidget {
  const CircleIconButton({
    super.key,
    required this.icon,
    required this.onPressed,
    this.size = 42.0,
    this.iconSize = 22.0,
  });

  final IconData icon;
  final VoidCallback onPressed;
  final double size;
  final double iconSize;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: AppColors.darkGreen,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.15),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: IconButton(
        onPressed: onPressed,
        icon: Icon(icon, color: AppColors.cardCream, size: iconSize),
        padding: EdgeInsets.zero,
      ),
    );
  }
}

// 2. Botón específico de Notificaciones
class NotificationButton extends StatelessWidget {
  const NotificationButton({super.key, required this.onPressed});
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return CircleIconButton(
      icon: Icons.notifications_outlined,
      onPressed: onPressed,
    );
  }
}

// 3. Botón específico de Perfil
class ProfileIconButton extends StatelessWidget {
  const ProfileIconButton({super.key, required this.onPressed});
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return CircleIconButton(
      icon: Icons.person_outline,
      onPressed: onPressed,
    );
  }
}