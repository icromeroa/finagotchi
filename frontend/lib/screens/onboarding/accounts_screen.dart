import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

class AccountsScreen extends StatefulWidget {
  const AccountsScreen({super.key});

  @override
  State<AccountsScreen> createState() => _AccountsScreenState();
}

class _AccountsScreenState extends State<AccountsScreen> {
  // Estado para alternar entre "Cuentas" y "Metas de ahorro"
  bool _isCuentasSelected = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // ===================================================================
            // 1. BARRA SUPERIOR (Versión y botones de perfil/notificación)
            // ===================================================================
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 4),
              child: Row(
                children: [
                  const Text(
                    'V14.1 Cuentas',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  // Botón Notificaciones
                  Container(
                    width: 38,
                    height: 38,
                    decoration: const BoxDecoration(
                      color: AppColors.darkGreen,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      onPressed: () {},
                      icon: const Icon(Icons.notifications_none, color: AppColors.cardCream, size: 18),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Botón Perfil
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      color: AppColors.wine,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.cardCream, width: 1.5),
                    ),
                    child: IconButton(
                      onPressed: () {},
                      icon: const Icon(Icons.person_outline, color: AppColors.cardCream, size: 18),
                      padding: EdgeInsets.zero,
                    ),
                  ),
                ],
              ),
            ),

            // ===================================================================
            // 2. PESTAÑAS (Cuentas y Metas de ahorro)
            // ===================================================================
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Container(
                height: 48,
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: () => setState(() => _isCuentasSelected = true),
                        child: Container(
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: _isCuentasSelected ? AppColors.wine : Colors.transparent,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            'Cuentas',
                            style: TextStyle(
                              color: _isCuentasSelected ? AppColors.cardCream : AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ),
                    ),
                    Expanded(
                      child: GestureDetector(
                        onTap: () => setState(() => _isCuentasSelected = false),
                        child: Container(
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: !_isCuentasSelected ? AppColors.wine : Colors.transparent,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            'Metas de ahorro',
                            style: TextStyle(
                              color: !_isCuentasSelected ? AppColors.cardCream : AppColors.wine,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ===================================================================
            // 3. TARJETA INFORMATIVA DE NANCY
            // ===================================================================
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.wine.withOpacity(0.12)),
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

            // ===================================================================
            // 4. CUADRÍCULA DE CUENTAS (GRID VIEW)
            // ===================================================================
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.35,
                children: [
                  _buildAccountCard(
                    icon: Icons.account_balance,
                    title: 'Nequi',
                    subtitle: '2 movs',
                    tagText: 'PREDET.',
                  ),
                  _buildAccountCard(
                    icon: Icons.account_balance,
                    title: 'Nu',
                    subtitle: '0 movs',
                    tagText: 'PREDET.',
                  ),
                  _buildAccountCard(
                    icon: Icons.account_balance,
                    title: 'Bancolombia',
                    subtitle: '1 mov',
                    tagText: 'PREDET.',
                  ),
                  _buildAccountCard(
                    icon: Icons.account_balance,
                    title: 'Daviplata',
                    subtitle: '1 mov',
                    tagText: 'PREDET.',
                  ),
                  _buildAccountCard(
                    icon: Icons.payments_outlined,
                    title: 'Efectivo',
                    subtitle: '2 movs',
                    hasTag: false,
                  ),
                  _buildCreateCard(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAccountCard({
    required IconData icon,
    required String title,
    required String subtitle,
    String? tagText,
    bool hasTag = true,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.wine.withOpacity(0.15)),
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
                  color: AppColors.mutedPink.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: AppColors.wine, size: 18),
              ),
              if (hasTag)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    tagText ?? '',
                    style: const TextStyle(
                      color: AppColors.wine,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 13.5,
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

  Widget _buildCreateCard() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.lime.withOpacity(0.6),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.darkGreen.withOpacity(0.2)),
      ),
      child: InkWell(
        onTap: () {
          // Acción para crear nueva cuenta
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