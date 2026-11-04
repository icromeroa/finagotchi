import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class OptionCard extends StatelessWidget {
  final String title;
  final String description;
  final String? letter;
  final IconData? icon;
  final bool selected;
  final VoidCallback onTap;

  const OptionCard({
    super.key,
    required this.title,
    this.description = '',
    this.letter,
    this.icon,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(13),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: selected
                ? const Color(0xFFEAF0D4)
                : AppColors.cardCream,
            borderRadius: BorderRadius.circular(13),
            border: Border.all(
              color: selected
                  ? AppColors.lime
                  : const Color(0xFFD7A0A9),
              width: selected ? 2 : 1,
            ),
            boxShadow: const [
              BoxShadow(
                color: AppColors.darkGreen,
                offset: Offset(0, 3),
              ),
            ],
          ),
          child: Row(
            children: [
              if (letter != null)
                Container(
                  width: 32,
                  height: 34,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: AppColors.cream,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: AppColors.mutedPink,
                    ),
                  ),
                  child: Text(
                    letter!,
                    style: const TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              if (icon != null)
                Container(
                  width: 40,
                  height: 40,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: AppColors.cream,
                    borderRadius: BorderRadius.circular(9),
                    border: Border.all(
                      color: AppColors.mutedPink,
                    ),
                  ),
                  child: Icon(
                    icon,
                    color: AppColors.wine,
                    size: 24,
                  ),
                ),
              if (letter != null || icon != null)
                const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        color: AppColors.darkGreen,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                    if (description.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: const TextStyle(
                          color: AppColors.darkGreen,
                          fontSize: 10,
                          height: 1.25,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (selected)
                const Icon(
                  Icons.check_circle,
                  color: AppColors.darkGreen,
                ),
            ],
          ),
        ),
      ),
    );
  }
}