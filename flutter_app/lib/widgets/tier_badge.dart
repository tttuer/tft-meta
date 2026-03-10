import 'package:flutter/material.dart';
import '../core/constants.dart';

class TierBadge extends StatelessWidget {
  final String tier;
  final double size;
  final bool compact;

  const TierBadge({
    super.key,
    required this.tier,
    this.size = 28,
    this.compact = false,
  });

  Color get _tierColor => tierColors[tier] ?? AppColors.textSecondary;

  @override
  Widget build(BuildContext context) {
    if (compact) {
      return Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: _tierColor.withAlpha(38),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: _tierColor, width: 1.5),
        ),
        alignment: Alignment.center,
        child: Text(
          tier,
          style: TextStyle(
            color: _tierColor,
            fontSize: size * 0.5,
            fontWeight: FontWeight.bold,
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: _tierColor.withAlpha(38),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _tierColor, width: 1.5),
      ),
      child: Text(
        '$tier 티어',
        style: TextStyle(
          color: _tierColor,
          fontSize: AppFontSizes.sm,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
