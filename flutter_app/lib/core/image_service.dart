import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import 'constants.dart';

/// TFT 이미지 위젯 헬퍼
/// API 응답의 image_url을 그대로 사용하고, 실패 시 이니셜 폴백을 표시한다.
class ImageService {
  ImageService._();

  /// 챔피언 초상화
  static Widget championImage(
    String? imageUrl, {
    double size = 48,
    String? fallbackName,
    BoxFit fit = BoxFit.cover,
  }) {
    if (imageUrl == null || imageUrl.isEmpty) {
      return _initials(fallbackName, size, AppColors.primary);
    }
    return CachedNetworkImage(
      imageUrl: imageUrl,
      width: size,
      height: size,
      fit: fit,
      placeholder: (_, __) => _shimmer(size),
      errorWidget: (_, __, ___) => _initials(fallbackName, size, AppColors.primary),
    );
  }

  /// 아이템 아이콘
  static Widget itemImage(
    String? imageUrl, {
    double size = 28,
    String? fallbackName,
  }) {
    if (imageUrl == null || imageUrl.isEmpty) {
      return _initials(fallbackName, size, AppColors.gold);
    }
    return CachedNetworkImage(
      imageUrl: imageUrl,
      width: size,
      height: size,
      fit: BoxFit.cover,
      placeholder: (_, __) => _shimmer(size),
      errorWidget: (_, __, ___) => _initials(fallbackName, size, AppColors.gold),
    );
  }

  /// 증강 아이콘
  static Widget augmentImage(
    String? imageUrl, {
    double size = 36,
    String? fallbackName,
  }) {
    if (imageUrl == null || imageUrl.isEmpty) {
      return _initials(fallbackName, size, AppColors.accent);
    }
    return CachedNetworkImage(
      imageUrl: imageUrl,
      width: size,
      height: size,
      fit: BoxFit.cover,
      placeholder: (_, __) => _shimmer(size),
      errorWidget: (_, __, ___) => _initials(fallbackName, size, AppColors.accent),
    );
  }

  /// 트레이트(시너지) 아이콘
  static Widget traitIcon(
    String? imageUrl, {
    double size = 24,
    String? fallbackName,
  }) {
    if (imageUrl == null || imageUrl.isEmpty) {
      return _initials(fallbackName, size, AppColors.textSecondary);
    }
    return CachedNetworkImage(
      imageUrl: imageUrl,
      width: size,
      height: size,
      fit: BoxFit.cover,
      placeholder: (_, __) => _shimmer(size),
      errorWidget: (_, __, ___) => _initials(fallbackName, size, AppColors.textSecondary),
    );
  }

  static Widget _shimmer(double size) {
    return Shimmer.fromColors(
      baseColor: AppColors.surface,
      highlightColor: AppColors.divider,
      child: Container(width: size, height: size, color: AppColors.surface),
    );
  }

  static Widget _initials(String? name, double size, Color color) {
    final label = name != null && name.isNotEmpty
        ? name.substring(0, name.length >= 2 ? 2 : 1).toUpperCase()
        : '?';
    return Container(
      width: size,
      height: size,
      color: color.withAlpha(40),
      child: Center(
        child: Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: size * 0.35,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
