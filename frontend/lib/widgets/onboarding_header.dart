import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class OnboardingHeader extends StatelessWidget {
  final int step;
  final VoidCallback? onBack;
  final VoidCallback? onSkip;

  const OnboardingHeader({
    super.key,
    required this.step,
    this.onBack,
    this.onSkip,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
      child: Column(
        children: [
          Row(
            children: [
              IconButton(
                onPressed: onBack,
                icon: const Icon(
                  Icons.arrow_back,
                  color: AppColors.wine,
                ),
              ),
              const Expanded(
                child: Text(
                  'Configura a Nancy',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ),
              TextButton(
                onPressed: onSkip,
                child: const Text(
                  'Skip',
                  style: TextStyle(
                    color: AppColors.wine,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: LinearProgressIndicator(
              value: step / 7,
              minHeight: 8,
              backgroundColor: AppColors.progressBackground,
              valueColor: const AlwaysStoppedAnimation(
                AppColors.lime,
              ),
            ),
          ),
        ],
      ),
    );
  }
}