
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

import 'personal_data_screen.dart';
import 'categories_screen.dart';
import 'security_screen.dart';
import 'improve_metrics_screen.dart';
import 'delete_account_screen.dart';
import 'streak_screen.dart';
import 'notifications_screen.dart';

import '../login_screen.dart';
import '../home_screen.dart';
import '../metrics_screen.dart';
import '../accounts_overview_screen.dart';
import 'device_link_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _notificacionesNancy = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // BARRA SUPERIOR
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1. BOTÓN DE RACHA
                  GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const StreakScreen(),
                        ),
                      );
                    },
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 14,
                            vertical: 7,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.cardCream,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: AppColors.wine,
                              width: 1.5,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: const [
                              Icon(
                                Icons.local_fire_department,
                                color: Colors.orange,
                                size: 18,
                              ),
                              SizedBox(width: 6),
                              Text(
                                '1 días',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 3),
                        const Padding(
                          padding: EdgeInsets.only(left: 4),
                          child: Text(
                            '• Registra hoy para mantenerla',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 9.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const Spacer(),

                  // 2. BOTÓN DE NOTIFICACIONES
                  Container(
                    width: 42,
                    height: 42,
                    decoration: const BoxDecoration(
                      color: AppColors.darkGreen,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                            const NotificationsScreen(),
                          ),
                        );
                      },
                      icon: const Icon(
                        Icons.notifications_none,
                        color: AppColors.cardCream,
                        size: 22,
                      ),
                      padding: EdgeInsets.zero,
                    ),
                  ),

                  const SizedBox(width: 10),

                  Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      color: AppColors.wine,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.cardCream,
                        width: 1.5,
                      ),
                    ),
                    child: IconButton(
                      onPressed: () {},
                      icon: const Icon(
                        Icons.person_outline,
                        color: AppColors.cardCream,
                        size: 22,
                      ),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                ],
              ),
            ),

            // CONTENIDO CON SCROLL
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
                child: Column(
                  children: [
                    // CABECERA DE USUARIO
                    Row(
                      children: [
                        Stack(
                          children: [
                            Container(
                              width: 60,
                              height: 60,
                              decoration: BoxDecoration(
                                color: AppColors.wine,
                                borderRadius: BorderRadius.circular(18),
                              ),
                              child: const Center(
                                child: Text(
                                  'IR',
                                  style: TextStyle(
                                    color: AppColors.cardCream,
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                            Positioned(
                              bottom: 0,
                              right: 0,
                              child: Container(
                                width: 20,
                                height: 20,
                                decoration: BoxDecoration(
                                  color: AppColors.lime,
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: AppColors.cardCream,
                                    width: 2,
                                  ),
                                ),
                                child: const Icon(
                                  Icons.edit,
                                  color: AppColors.darkGreen,
                                  size: 10,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(width: 14),
                        const Text(
                          'Irene Romero',
                          style: TextStyle(
                            color: AppColors.wine,
                            fontSize: 20,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 14),

                    // TARJETAS DE ESTADÍSTICAS
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: AppColors.cardCream,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: AppColors.wine.withOpacity(0.15),
                              ),
                            ),
                            child: Column(
                              children: const [
                                Text(
                                  'Racha',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  '24 días',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontSize: 18,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: AppColors.cardCream,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: AppColors.wine.withOpacity(0.15),
                              ),
                            ),
                            child: Column(
                              children: const [
                                Text(
                                  'Ahorro Mes',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  '+\$480',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontSize: 18,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 14),

                    // 1. INFORMACIÓN PERSONAL
                    _buildProfileItem(
                      icon: Icons.badge_outlined,
                      title: 'Información Personal',
                      subtitle: 'Nombre completo, correo',
                      onTap: () {
                        showModalBottomSheet(
                          context: context,
                          isScrollControlled: true,
                          backgroundColor: Colors.transparent,
                          builder: (context) =>
                          const PersonalDataScreen(),
                        );
                      },
                    ),

                    const SizedBox(height: 10),

                    // 2. CATEGORÍAS
                    _buildProfileItem(
                      icon: Icons.folder_open_outlined,
                      title: 'Categorías',
                      subtitle: 'Revisa y crea nuevas categorías',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const CategoriesScreen(),
                          ),
                        );
                      },
                    ),

                    const SizedBox(height: 10),

                    // 3. CUENTAS
                    _buildProfileItem(
                      icon: Icons.account_balance_wallet_outlined,
                      title: 'Cuentas',
                      subtitle: 'Tus medios de pago',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                            const AccountsOverviewScreen(),
                          ),
                        );
                      },
                    ),

                    const SizedBox(height: 10),

                    // 4. SEGURIDAD Y CLAVE
                    _buildProfileItem(
                      icon: Icons.lock_outline,
                      title: 'Seguridad y Clave',
                      subtitle: 'Contraseña protegida',
                      onTap: () {
                        showModalBottomSheet(
                          context: context,
                          isScrollControlled: true,
                          backgroundColor: Colors.transparent,
                          builder: (context) => const SecurityScreen(),
                        );
                      },
                    ),

                    const SizedBox(height: 10),

                    // 5. MEJORA TUS MÉTRICAS
                    _buildProfileItem(
                      icon: Icons.auto_graph_outlined,
                      title: 'Mejora tus métricas',
                      subtitle: 'Completa tu info y Nancy mejora',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                            const ImproveMetricsScreen(),
                          ),
                        );
                      },
                    ),

                    const SizedBox(height: 10),

                    // NOTIFICACIONES DE NANCY
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: AppColors.wine.withOpacity(0.15),
                        ),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.mutedPink,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.notifications_active_outlined,
                              color: AppColors.wine,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Notificaciones de Nancy',
                                  style: TextStyle(
                                    color: AppColors.wine,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13.5,
                                  ),
                                ),
                                Text(
                                  'Avisos de hambre y quests diarias',
                                  style: TextStyle(
                                    color: AppColors.darkGreen,
                                    fontSize: 10.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Switch(
                            value: _notificacionesNancy,
                            onChanged: (val) {
                              setState(() {
                                _notificacionesNancy = val;
                              });
                            },
                            activeColor: AppColors.cardCream,
                            activeTrackColor: AppColors.lime,
                            inactiveThumbColor: AppColors.cardCream,
                            inactiveTrackColor: Colors.grey,
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 10),

                    // VINCULAR DISPOSITIVO (PIN simulador)
                    _buildProfileItem(
                      icon: Icons.link,
                      title: 'Vincular dispositivo',
                      subtitle: 'Enlaza con el simulador usando el PIN',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const DeviceLinkScreen(),
                          ),
                        );
                      },
                    ),

                    const SizedBox(height: 10),

                    // 6. ELIMINAR CUENTA
                    _buildProfileItem(
                      icon: Icons.warning_amber_rounded,
                      title: 'Eliminar Cuenta',
                      subtitle: 'Borrar mascota y datos de ahorro',
                      isDestructive: true,
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                            const DeleteAccountScreen(),
                          ),
                        );
                      },
                    ),

                    const SizedBox(height: 16),

                    // CERRAR SESIÓN
                    Center(
                      child: Container(
                        height: 46,
                        width: 200,
                        decoration: BoxDecoration(
                          color: AppColors.mutedPink,
                          borderRadius: BorderRadius.circular(23),
                          border: Border.all(
                            color: AppColors.wine,
                            width: 1.5,
                          ),
                        ),
                        child: InkWell(
                          onTap: () {
                            Navigator.pushAndRemoveUntil(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const LoginScreen(),
                              ),
                                  (route) => false,
                            );
                          },
                          borderRadius: BorderRadius.circular(23),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: const [
                              Text(
                                'Cerrar sesión',
                                style: TextStyle(
                                  color: AppColors.wine,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13.5,
                                ),
                              ),
                              SizedBox(width: 6),
                              Icon(
                                Icons.logout,
                                color: AppColors.wine,
                                size: 16,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 14),

                    const Text(
                      'Construido con <3',
                      style: TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // BARRA INFERIOR
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.cardCream,
                        borderRadius: BorderRadius.circular(30),
                        border: Border.all(
                          color: AppColors.darkGreen,
                          width: 2,
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildNavItem(
                            icon: Icons.home_outlined,
                            label: 'Inicio',
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => const HomeScreen(),
                                ),
                              );
                            },
                          ),
                          _buildNavItem(
                            icon: Icons.bar_chart_rounded,
                            label: 'Métricas',
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => const MetricsScreen(),
                                ),
                              );
                            },
                          ),
                          _buildNavItem(
                            icon: Icons.account_balance_wallet_outlined,
                            label: 'Cuentas',
                            isSelected: false,
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) =>
                                  const AccountsOverviewScreen(),
                                ),
                              );
                            },
                          ),
                          _buildNavItem(
                            icon: Icons.find_in_page_outlined,
                            label: 'Historial',
                            isSelected: false,
                            onTap: () {},
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    width: 50,
                    height: 50,
                    decoration: BoxDecoration(
                      color: AppColors.lime,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.darkGreen,
                        width: 2,
                      ),
                    ),
                    child: IconButton(
                      onPressed: () {},
                      icon: const Icon(
                        Icons.support_agent,
                        color: AppColors.darkGreen,
                        size: 24,
                      ),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // CONSTRUCTOR DE OPCIONES DEL PERFIL
  Widget _buildProfileItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
    bool isDestructive = false,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: isDestructive
            ? AppColors.mutedPink.withOpacity(0.4)
            : AppColors.cardCream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDestructive
              ? Colors.red.withOpacity(0.3)
              : AppColors.wine.withOpacity(0.15),
        ),
      ),
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 2,
        ),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: isDestructive
                ? Colors.red.shade100
                : AppColors.mutedPink,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            icon,
            color: isDestructive
                ? Colors.red.shade700
                : AppColors.wine,
            size: 20,
          ),
        ),
        title: Text(
          title,
          style: TextStyle(
            color: isDestructive
                ? Colors.red.shade900
                : AppColors.wine,
            fontWeight: FontWeight.bold,
            fontSize: 13.5,
          ),
        ),
        subtitle: Text(
          subtitle,
          style: TextStyle(
            color: isDestructive
                ? Colors.red.shade700
                : AppColors.darkGreen,
            fontSize: 10.5,
          ),
        ),
        trailing: Icon(
          Icons.arrow_forward_ios,
          color: isDestructive
              ? Colors.red.shade700
              : AppColors.wine,
          size: 14,
        ),
      ),
    );
  }

  // CONSTRUCTOR DE NAVEGACIÓN INFERIOR
  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: 4,
          vertical: 2,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected
                  ? AppColors.lime
                  : AppColors.darkGreen,
              size: 24,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                color: isSelected
                    ? AppColors.lime
                    : AppColors.darkGreen,
                fontSize: 10,
                fontWeight: isSelected
                    ? FontWeight.bold
                    : FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
