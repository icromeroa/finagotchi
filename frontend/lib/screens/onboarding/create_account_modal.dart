import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../widgets/finagotchi_dialogs.dart';

class CreateAccountModal extends StatefulWidget {
  const CreateAccountModal({super.key});

  @override
  State<CreateAccountModal> createState() => _CreateAccountModalState();
}

class _CreateAccountModalState extends State<CreateAccountModal> {
  String _accountName = 'Débito Bancolombia';
  int _selectedAccountType = 0;
  int _selectedIconIndex = 0;
  bool _useByDefault = false;

  final List<String> _magicWords = ['débito', 'la débito', 'con tarjeta'];

  final _accountTypes = [
    {'title': 'Tarjeta', 'subtitle': 'Débito o crédito', 'icon': Icons.credit_card},
    {'title': 'Efectivo', 'subtitle': 'Billetera física', 'icon': Icons.wallet_outlined},
    {'title': 'Bancaria', 'subtitle': 'Cuenta de ahorros', 'icon': Icons.account_balance_outlined},
    {'title': 'Billetera Digital', 'subtitle': 'Cuenta de ahorros', 'icon': Icons.account_balance_wallet_outlined},
    {'title': 'Inversión', 'subtitle': 'Fondos y metas', 'icon': Icons.trending_up},
  ];

  final List<IconData> _previewIcons = [
    Icons.credit_card,
    Icons.wallet,
    Icons.savings_outlined,
    Icons.shopping_bag_outlined,
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.90,
      ),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ===================================================
          // ENCABEZADO
          // ===================================================
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: AppColors.wine,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.grid_view_rounded, color: AppColors.cardCream, size: 18),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'Crear cuenta',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
              GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: AppColors.mutedPink,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.close, color: AppColors.wine, size: 18),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // ===================================================
          // CONTENIDO SCROLLABLE
          // ===================================================
          Flexible(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ------------------------------------------------
                  // SECCIÓN 1: LO BÁSICO
                  // ------------------------------------------------
                  _buildSectionHeader('1', 'Lo básico', 'REQUERIDO'),
                  const SizedBox(height: 8),
                  const Text(
                    'Nombre de la cuenta',
                    style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: AppColors.cardCream,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.wine.withOpacity(0.2)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          _accountName,
                          style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        Text(
                          '${_accountName.length}/24',
                          style: const TextStyle(color: AppColors.wine, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Tipo de cuenta',
                    style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),

                  // Grid de tipos de cuenta
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _accountTypes.length,
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                      childAspectRatio: 2.1,
                    ),
                    itemBuilder: (context, index) {
                      final item = _accountTypes[index];
                      final isSelected = _selectedAccountType == index;
                      return GestureDetector(
                        onTap: () => setState(() => _selectedAccountType = index),
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: isSelected ? AppColors.wine : AppColors.cardCream,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: isSelected ? AppColors.wine : AppColors.wine.withOpacity(0.15),
                              width: isSelected ? 1.5 : 1,
                            ),
                          ),
                          child: Stack(
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    item['icon'] as IconData,
                                    color: isSelected ? AppColors.cardCream : AppColors.wine,
                                    size: 20,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    item['title'] as String,
                                    style: TextStyle(
                                      color: isSelected ? AppColors.cardCream : AppColors.wine,
                                      fontWeight: FontWeight.w900,
                                      fontSize: 12,
                                    ),
                                  ),
                                  Text(
                                    item['subtitle'] as String,
                                    style: TextStyle(
                                      color: isSelected ? AppColors.cardCream.withOpacity(0.8) : AppColors.darkGreen,
                                      fontSize: 9.5,
                                    ),
                                  ),
                                ],
                              ),
                              if (isSelected)
                                const Positioned(
                                  top: 0,
                                  right: 0,
                                  child: Icon(Icons.check_circle, color: AppColors.lime, size: 16),
                                ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 16),

                  // ------------------------------------------------
                  // SECCIÓN 2: CÓMO SE VE (CON FONDO ROSADO)
                  // ------------------------------------------------
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink.withOpacity(0.45),
                      borderRadius: BorderRadius.circular(22),
                      border: Border.all(color: AppColors.wine.withOpacity(0.12)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildSectionHeader('2', 'Cómo se ve', 'OPCIONAL'),
                        const SizedBox(height: 12),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(
                              width: 88,
                              child: Column(
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      _buildIconSelectorBox(_previewIcons[0], 0),
                                      _buildIconSelectorBox(_previewIcons[1], 1),
                                    ],
                                  ),
                                  const SizedBox(height: 6),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      _buildIconSelectorBox(_previewIcons[2], 2),
                                      _buildIconSelectorBox(_previewIcons[3], 3),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: AppColors.cardCream,
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(color: AppColors.darkGreen, width: 1.2),
                                ),
                                child: Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: AppColors.mutedPink,
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                      child: Icon(_previewIcons[_selectedIconIndex], color: AppColors.wine, size: 16),
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            _accountName,
                                            style: const TextStyle(
                                              color: AppColors.wine,
                                              fontWeight: FontWeight.bold,
                                              fontSize: 11,
                                            ),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                          const SizedBox(height: 2),
                                          const Text(
                                            '0 movs',
                                            style: TextStyle(color: AppColors.darkGreen, fontSize: 9.5, fontWeight: FontWeight.bold),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // ------------------------------------------------
                  // SECCIÓN 3: SALDO (CON FONDO BEIGE)
                  // ------------------------------------------------
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.cardCream,
                      borderRadius: BorderRadius.circular(22),
                      border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildSectionHeader('3', 'Saldo', 'OPCIONAL'),
                        const SizedBox(height: 10),
                        const Text(
                          'Últimos 4 dígitos',
                          style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 6),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          decoration: BoxDecoration(
                            color: AppColors.cream,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: AppColors.wine.withOpacity(0.2)),
                          ),
                          child: const Text(
                            '8821',
                            style: TextStyle(
                              color: AppColors.wine,
                              fontWeight: FontWeight.w900,
                              fontSize: 20,
                              letterSpacing: 2,
                            ),
                          ),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Solo para que la reconozcas. Nunca te pedimos el número completo.',
                          style: TextStyle(
                            color: AppColors.darkGreen,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.cream,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: AppColors.darkGreen, width: 1.5),
                          ),
                          child: Row(
                            children: const [
                              Icon(Icons.info_outline, color: AppColors.darkGreen, size: 18),
                              SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  'Las tarjetas no llevan saldo: sus compras se suman a tus gastos del mes.',
                                  style: TextStyle(color: AppColors.darkGreen, fontSize: 11, height: 1.3),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // ------------------------------------------------
                  // SECCIÓN 4: CÓMO LA USA NANCY (CON FONDO BEIGE)
                  // ------------------------------------------------
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.cardCream,
                      borderRadius: BorderRadius.circular(22),
                      border: Border.all(color: AppColors.wine.withOpacity(0.15)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildSectionHeader('4', 'Cómo la usa Nancy', 'OPCIONAL'),
                        const SizedBox(height: 10),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Usar cuando no diga la cuenta',
                                  style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 11.5),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'Ahora uso Efectivo.',
                                  style: TextStyle(color: AppColors.darkGreen, fontSize: 10.5),
                                ),
                              ],
                            ),
                            Switch(
                              value: _useByDefault,
                              activeColor: AppColors.cardCream,
                              activeTrackColor: AppColors.darkGreen,
                              onChanged: (val) => setState(() => _useByDefault = val),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Palabras mágicas',
                              style: TextStyle(color: AppColors.wine, fontWeight: FontWeight.bold, fontSize: 11),
                            ),
                            Text(
                              '${_magicWords.length} de 5',
                              style: TextStyle(color: AppColors.darkGreen, fontSize: 10, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            ..._magicWords.map((word) => Chip(
                              backgroundColor: AppColors.cream,
                              deleteIconColor: AppColors.wine,
                              onDeleted: () {
                                setState(() => _magicWords.remove(word));
                              },
                              label: Text(
                                word,
                                style: const TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                                side: BorderSide(color: AppColors.wine.withOpacity(0.2)),
                              ),
                            )),
                            ActionChip(
                              backgroundColor: AppColors.mutedPink,
                              onPressed: () {
                                setState(() {
                                  _magicWords.add('nueva palabra');
                                });
                              },
                              label: const Text(
                                '+ Añadir',
                                style: TextStyle(color: AppColors.wine, fontSize: 11, fontWeight: FontWeight.bold),
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                                side: BorderSide(color: AppColors.wine.withOpacity(0.2)),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Las sugerí con el nombre. Quítalas o agrega las tuyas.',
                          style: TextStyle(color: AppColors.darkGreen, fontSize: 9.5),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),

          // ===================================================
          // BOTÓN INFERIOR: CREAR CUENTA (ABRE MODAL DE ÉXITO)
          // ===================================================
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: () {
                // 1. Cierra el modal actual de creación de cuenta
                Navigator.pop(context);

                // 2. Muestra el modal de éxito unificado que creamos en FinaGotchiDialogs
                FinaGotchiDialogs.showCreatedSuccess(
                  context,
                  onEntendido: () {
                    // Acciones opcionales al presionar "Entendido"
                  },
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.lime,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(25),
                  side: BorderSide(color: AppColors.darkGreen.withOpacity(0.3), width: 1.5),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Text(
                    'Crear cuenta',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontWeight: FontWeight.w900,
                      fontSize: 15,
                    ),
                  ),
                  SizedBox(width: 6),
                  Icon(Icons.check, color: AppColors.darkGreen, size: 18),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),
          Center(
            child: GestureDetector(
              onTap: () => Navigator.pop(context),
              child: const Text(
                'Cancelar',
                style: TextStyle(
                  color: AppColors.wine,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String number, String title, String badge) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Container(
              width: 22,
              height: 22,
              decoration: const BoxDecoration(
                color: AppColors.wine,
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Text(
                number,
                style: const TextStyle(color: AppColors.cardCream, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              title,
              style: const TextStyle(color: AppColors.wine, fontWeight: FontWeight.w900, fontSize: 14),
            ),
          ],
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
          decoration: BoxDecoration(
            color: AppColors.cardCream,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppColors.wine.withOpacity(0.15)),
          ),
          child: Text(
            badge,
            style: const TextStyle(
              color: AppColors.wine,
              fontSize: 9.5,
              fontWeight: FontWeight.w900,
              letterSpacing: 0.5,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildIconSelectorBox(IconData icon, int index) {
    final isSelected = _selectedIconIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _selectedIconIndex = index),
      child: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          color: isSelected ? AppColors.wine : AppColors.cardCream,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isSelected ? AppColors.wine : AppColors.wine.withOpacity(0.2),
          ),
        ),
        child: Icon(
          icon,
          color: isSelected ? AppColors.cardCream : AppColors.wine,
          size: 18,
        ),
      ),
    );
  }
}