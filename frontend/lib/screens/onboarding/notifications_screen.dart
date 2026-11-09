
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import 'count_perfil.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  String _currentState = 'normal';
  String _selectedTab = 'Todos';

  // Lista de notificaciones de prueba
  final List<Map<String, dynamic>> _notifications = [
    {
      'id': '1',
      'title': 'Café',
      'subtitle': 'Efectivo · 1:15 PM',
      'amount': '-\$16.000',
      'time': '1:15 p. m.',
      'isNegative': true,
      'icon': Icons.local_cafe_outlined,
      'bgColor': AppColors.mutedPink,
    },
    {
      'id': '2',
      'title': 'Almuerzo corriente',
      'subtitle': 'Restaurante · Nequi',
      'amount': '-\$14.000',
      'time': '4:32 p. m.',
      'isNegative': true,
      'icon': Icons.fastfood_outlined,
      'bgColor': AppColors.mutedPink,
    },
    {
      'id': '3',
      'title': 'Aporte a Viaje Eje ...',
      'subtitle': 'Meta ahorro · Bancolomb',
      'amount': '+\$50.000',
      'time': '2:15 p. m.',
      'isNegative': false,
      'icon': Icons.savings_outlined,
      'bgColor': AppColors.lime,
    },
    {
      'id': '4',
      'title': 'Gasto en Farmacia',
      'subtitle': '¿Lo entendí bien?',
      'amount': '-\$7.000',
      'time': '11:20 a. m.',
      'isNegative': true,
      'icon': Icons.help_outline,
      'bgColor': Colors.amber,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // BARRA SUPERIOR
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
              child: Row(
                children: [
                  const Icon(
                    Icons.notifications_active_outlined,
                    color: AppColors.wine,
                    size: 26,
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Avisos',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 26,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const Spacer(),
                  Stack(
                    children: [
                      Container(
                        width: 42,
                        height: 42,
                        decoration: const BoxDecoration(
                          color: AppColors.wine,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.notifications,
                          color: AppColors.cardCream,
                          size: 22,
                        ),
                      ),
                      Positioned(
                        top: 8,
                        right: 8,
                        child: Container(
                          width: 9,
                          height: 9,
                          decoration: BoxDecoration(
                            color: Colors.amber.shade400,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: AppColors.wine,
                              width: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(width: 10),
                  GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const ProfileScreen(),
                        ),
                      );
                    },
                    child: Container(
                      width: 42,
                      height: 42,
                      decoration: const BoxDecoration(
                        color: AppColors.darkGreen,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.person_outline,
                        color: AppColors.cardCream,
                        size: 22,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // SELECTOR DE PRUEBA
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 4,
              ),
              color: AppColors.mutedPink.withOpacity(0.3),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    'Estado UI: ',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: AppColors.wine,
                    ),
                  ),
                  DropdownButton<String>(
                    value: _currentState,
                    isDense: true,
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                    ),
                    dropdownColor: AppColors.cardCream,
                    items: const [
                      DropdownMenuItem(
                        value: 'normal',
                        child: Text('Normal (Con avisos)'),
                      ),
                      DropdownMenuItem(
                        value: 'vacias',
                        child: Text('Vacías'),
                      ),
                      DropdownMenuItem(
                        value: 'aldia',
                        child: Text('Al día'),
                      ),
                      DropdownMenuItem(
                        value: 'cargando',
                        child: Text('Cargando..'),
                      ),
                      DropdownMenuItem(
                        value: 'error',
                        child: Text('Error'),
                      ),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        setState(() => _currentState = val);
                      }
                    },
                  ),
                ],
              ),
            ),

            // RESUMEN SUPERIOR
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 8,
              ),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.wine.withOpacity(0.15),
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.smart_toy_outlined,
                          color: AppColors.darkGreen,
                          size: 18,
                        ),
                        const SizedBox(width: 6),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: const [
                            Text(
                              'Hoy desde tu',
                              style: TextStyle(
                                fontSize: 9.5,
                                color: AppColors.darkGreen,
                              ),
                            ),
                            Text(
                              'FinaGotchi',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: AppColors.wine,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    Row(
                      children: const [
                        _StatBadge(label: '4 registros'),
                        SizedBox(width: 6),
                        _StatBadge(label: '-\$21.000', isNegative: true),
                        SizedBox(width: 6),
                        _StatBadge(label: '+\$0'),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            // INDICADOR DE AVISOS
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 4,
              ),
              child: Row(
                children: [
                  const Text(
                    '● 3 sin leer',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () {},
                    child: const Text(
                      'Marcar todo como leído',
                      style: TextStyle(
                        color: AppColors.wine,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 4),

            // PESTAÑAS DE FILTRO
            SizedBox(
              height: 38,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  _buildTabButton('Todos'),
                  const SizedBox(width: 8),
                  _buildTabButton('Sin leer (3)'),
                  const SizedBox(width: 8),
                  _buildTabButton('Movimientos (4)'),
                ],
              ),
            ),
            const SizedBox(height: 8),

            // CUERPO DINÁMICO
            Expanded(
              child: _buildBodyContent(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTabButton(String title) {
    final isSelected = _selectedTab == title;

    return GestureDetector(
      onTap: () => setState(() => _selectedTab = title),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 8,
        ),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.wine : AppColors.cardCream,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: AppColors.wine.withOpacity(0.3),
          ),
        ),
        child: Text(
          title,
          style: TextStyle(
            color: isSelected
                ? AppColors.cardCream
                : AppColors.wine,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _buildBodyContent() {
    switch (_currentState) {
      case 'vacias':
        return _buildEmptyState();
      case 'aldia':
        return _buildUpToDateState();
      case 'cargando':
        return _buildLoadingState();
      case 'error':
        return _buildErrorState();
      case 'normal':
      default:
        return _buildNormalListState();
    }
  }

  Widget _buildNormalListState() {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
      children: [
        _buildSectionHeader(
          'Hoy · dom 25 oct',
          '${_notifications.length} avisos',
        ),
        const SizedBox(height: 8),
        ..._notifications.map((item) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Dismissible(
              key: Key(item['id'].toString()),
              direction: DismissDirection.endToStart,
              background: Container(
                alignment: Alignment.centerRight,
                decoration: BoxDecoration(
                  color: Colors.transparent,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 75,
                      height: double.infinity,
                      decoration: const BoxDecoration(
                        color: AppColors.mutedPink,
                        borderRadius: BorderRadius.only(
                          topLeft: Radius.circular(16),
                          bottomLeft: Radius.circular(16),
                        ),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(
                            Icons.check_circle_outline,
                            color: AppColors.wine,
                            size: 20,
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Leído',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      width: 75,
                      height: double.infinity,
                      decoration: const BoxDecoration(
                        color: AppColors.wine,
                        borderRadius: BorderRadius.only(
                          topRight: Radius.circular(16),
                          bottomRight: Radius.circular(16),
                        ),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(
                            Icons.delete_outline,
                            color: AppColors.cardCream,
                            size: 20,
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Eliminar',
                            style: TextStyle(
                              color: AppColors.cardCream,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              onDismissed: (direction) {
                setState(() {
                  _notifications.removeWhere(
                        (element) => element['id'] == item['id'],
                  );
                });

                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      'Notificación "${item['title']}" eliminada',
                    ),
                  ),
                );
              },
              child: GestureDetector(
                onTap: () => _showTransactionDetailModal(context, item),
                child: _buildNotificationCard(
                  icon: item['icon'] as IconData,
                  iconColor: (item['isNegative'] as bool)
                      ? AppColors.wine
                      : AppColors.darkGreen,
                  bgColor: item['bgColor'] as Color,
                  title: item['title'] as String,
                  subtitle: item['subtitle'] as String,
                  amount: item['amount'] as String,
                  time: item['time'] as String,
                  isNegative: item['isNegative'] as bool,
                ),
              ),
            ),
          );
        }),
        const SizedBox(height: 8),
        _buildSectionHeader('Ayer · sáb 24 oct', '2 avisos'),
      ],
    );
  }

  void _showTransactionDetailModal(
      BuildContext context,
      Map<String, dynamic> item,
      ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: const BorderRadius.vertical(
              top: Radius.circular(30),
            ),
            border: Border.all(
              color: AppColors.wine.withOpacity(0.2),
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.wine.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  const Text(
                    'Detalle Movimiento',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Container(
                      width: 32,
                      height: 32,
                      decoration: const BoxDecoration(
                        color: AppColors.mutedPink,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.close,
                        color: AppColors.wine,
                        size: 18,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              Container(
                width: 60,
                height: 60,
                decoration: const BoxDecoration(
                  color: AppColors.mutedPink,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.restaurant_menu,
                  color: AppColors.wine,
                  size: 28,
                ),
              ),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    item['amount'].toString(),
                    style: const TextStyle(
                      color: AppColors.wine,
                      fontSize: 24,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(width: 4),
                  const Icon(
                    Icons.arrow_outward,
                    color: AppColors.wine,
                    size: 20,
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                item['title'].toString(),
                style: const TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: AppColors.mutedPink.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    Icon(Icons.mic, color: AppColors.wine, size: 14),
                    SizedBox(width: 4),
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
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.cardCream,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: AppColors.wine.withOpacity(0.1),
                  ),
                ),
                child: Column(
                  children: [
                    _buildDetailRow(
                      label: 'Tipo',
                      value: 'Gasto',
                      icon: Icons.arrow_downward,
                      isWine: true,
                    ),
                    const Divider(height: 20, color: AppColors.cream),
                    _buildDetailRow(
                      label: 'Categoría',
                      value: 'Alimentación',
                      icon: Icons.restaurant,
                      isWine: false,
                    ),
                    const Divider(height: 20, color: AppColors.cream),
                    _buildDetailRow(
                      label: 'Medio de pago',
                      value: 'Nequi',
                      icon: Icons.account_balance_wallet_outlined,
                      isWine: false,
                    ),
                    const Divider(height: 20, color: AppColors.cream),
                    _buildDetailRow(
                      label: 'Fecha y hora',
                      value: 'Hoy, 24 oct · 12:40 pm',
                      icon: Icons.access_time,
                      isWine: false,
                    ),
                    const Divider(height: 20, color: AppColors.cream),
                    _buildDetailRow(
                      label: 'Origen',
                      value: 'Por voz (Dispositivo físico FinaGotchi)',
                      icon: Icons.devices,
                      isWine: false,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.lime,
                    foregroundColor: AppColors.darkGreen,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(25),
                      side: const BorderSide(
                        color: AppColors.darkGreen,
                        width: 1.5,
                      ),
                    ),
                  ),
                  child: const Text(
                    'Editar movimiento',
                    style: TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 14,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 14),
              GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: const [
                    Icon(
                      Icons.delete_outline,
                      color: AppColors.wine,
                      size: 16,
                    ),
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
            ],
          ),
        );
      },
    );
  }

  Widget _buildDetailRow({
    required String label,
    required String value,
    required IconData icon,
    required bool isWine,
  }) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: AppColors.darkGreen,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        Row(
          children: [
            Icon(
              icon,
              size: 14,
              color: isWine ? AppColors.wine : AppColors.darkGreen,
            ),
            const SizedBox(width: 4),
            Text(
              value,
              style: TextStyle(
                color: isWine ? AppColors.wine : AppColors.darkGreen,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Sin avisos por ahora',
              style: TextStyle(
                color: AppColors.wine,
                fontSize: 18,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Aquí te contaré lo que registres con tu FinaGotchi.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.darkGreen,
                fontSize: 11.5,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 16),
            GestureDetector(
              onTap: () {},
              child: const Text(
                'Configurar avisos',
                style: TextStyle(
                  color: AppColors.wine,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildUpToDateState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: const BoxDecoration(
                color: AppColors.darkGreen,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check,
                color: AppColors.cardCream,
                size: 30,
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              '¡Estás al día!',
              style: TextStyle(
                color: AppColors.wine,
                fontSize: 20,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'Has revisado todos tus registros y avisos sincronizados.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.darkGreen,
                fontSize: 11.5,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 14,
                vertical: 6,
              ),
              decoration: BoxDecoration(
                color: AppColors.lime.withOpacity(0.4),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Icon(
                    Icons.check,
                    color: AppColors.darkGreen,
                    size: 14,
                  ),
                  SizedBox(width: 4),
                  Text(
                    'Todo leído',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
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

  Widget _buildLoadingState() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildSkeletonCard(),
        const SizedBox(height: 12),
        _buildSkeletonCard(),
        const SizedBox(height: 12),
        _buildSkeletonCard(),
      ],
    );
  }

  Widget _buildSkeletonCard() {
    return Container(
      height: 70,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.cardCream.withOpacity(0.6),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppColors.mutedPink.withOpacity(0.5),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 120,
                  height: 12,
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
                const SizedBox(height: 6),
                Container(
                  width: 80,
                  height: 10,
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: Colors.amber.shade200,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.priority_high,
                color: AppColors.wine,
                size: 30,
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'No pudimos cargar tus avisos',
              style: TextStyle(
                color: AppColors.wine,
                fontSize: 18,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'Ocurrió un problema de sincronización con tu base local.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.darkGreen,
                fontSize: 11.5,
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {},
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.wine,
                foregroundColor: AppColors.cardCream,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 10,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Icon(Icons.refresh, size: 16),
                  SizedBox(width: 6),
                  Text(
                    'Reintentar',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
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

  Widget _buildSectionHeader(String title, String count) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: AppColors.wine,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          count,
          style: const TextStyle(
            color: AppColors.darkGreen,
            fontSize: 11,
          ),
        ),
      ],
    );
  }

  Widget _buildNotificationCard({
    required IconData icon,
    required Color iconColor,
    required Color bgColor,
    required String title,
    required String subtitle,
    required String amount,
    required String time,
    bool isNegative = true,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.12),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: bgColor,
              shape: BoxShape.circle,
            ),
            child: Icon(
              icon,
              color: iconColor,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    color: AppColors.darkGreen,
                    fontSize: 10.5,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                amount,
                style: TextStyle(
                  color: isNegative
                      ? AppColors.wine
                      : AppColors.darkGreen,
                  fontWeight: FontWeight.w900,
                  fontSize: 12.5,
                ),
              ),
              const SizedBox(height: 2),
              Row(
                children: [
                  const Icon(
                    Icons.smart_toy_outlined,
                    size: 10,
                    color: AppColors.darkGreen,
                  ),
                  const SizedBox(width: 3),
                  Text(
                    time,
                    style: const TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 9.5,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatBadge extends StatelessWidget {
  final String label;
  final bool isNegative;

  const _StatBadge({
    required this.label,
    this.isNegative = false,
  });

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: TextStyle(
        color: isNegative
            ? AppColors.wine
            : AppColors.darkGreen,
        fontSize: 10.5,
        fontWeight: FontWeight.bold,
      ),
    );
  }
}
