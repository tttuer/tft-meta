import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../core/constants.dart';

class ItemIcon extends StatelessWidget {
  final String itemId;
  final String? itemName;
  final String? imageUrl;
  final double size;

  const ItemIcon({
    super.key,
    required this.itemId,
    this.itemName,
    this.imageUrl,
    this.size = BoardConstants.itemSize,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: AppColors.gold, width: 1),
        color: AppColors.surface,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(3),
        child: imageUrl != null
            ? CachedNetworkImage(
                imageUrl: imageUrl!,
                fit: BoxFit.cover,
                errorWidget: (context, url, error) => _fallback(),
              )
            : _fallback(),
      ),
    );
  }

  Widget _fallback() {
    return Container(
      color: AppColors.primary.withAlpha(128),
      child: Center(
        child: Text(
          (itemName ?? itemId).substring(0, 1).toUpperCase(),
          style: TextStyle(
            color: AppColors.gold,
            fontSize: size * 0.5,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
