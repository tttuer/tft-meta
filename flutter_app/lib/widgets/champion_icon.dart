import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../core/constants.dart';

class ChampionIcon extends StatelessWidget {
  final String championId;
  final String? championName;
  final int cost;
  final String? imageUrl;
  final double size;
  final bool showBorder;
  final bool isCore;
  final int starLevel;

  const ChampionIcon({
    super.key,
    required this.championId,
    this.championName,
    required this.cost,
    this.imageUrl,
    this.size = 48,
    this.showBorder = true,
    this.isCore = false,
    this.starLevel = 1,
  });

  Color get _borderColor {
    if (isCore) return AppColors.gold;
    return costColors[cost] ?? AppColors.textSecondary;
  }

  double get _borderWidth => isCore ? 2.5 : 2.0;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size + (starLevel > 1 ? 12 : 0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (starLevel > 1)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                starLevel,
                (i) => Icon(
                  Icons.star,
                  size: BoardConstants.starSize,
                  color: starLevel == 3
                      ? AppColors.gold
                      : AppColors.textSecondary,
                ),
              ),
            ),
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: showBorder
                  ? Border.all(color: _borderColor, width: _borderWidth)
                  : null,
              color: AppColors.surface,
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: imageUrl != null
                  ? CachedNetworkImage(
                      imageUrl: imageUrl!,
                      fit: BoxFit.cover,
                      placeholder: (context, url) => _placeholder(),
                      errorWidget: (context, url, error) => _fallback(),
                    )
                  : _fallback(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _placeholder() {
    return Container(
      color: AppColors.surface,
      child: const Center(
        child: SizedBox(
          width: 16,
          height: 16,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
    );
  }

  Widget _fallback() {
    return Container(
      color: costColors[cost]?.withAlpha(51) ?? AppColors.surface,
      child: Center(
        child: Text(
          (championName ?? championId).substring(0, 1).toUpperCase(),
          style: TextStyle(
            color: costColors[cost] ?? AppColors.textPrimary,
            fontSize: size * 0.4,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
