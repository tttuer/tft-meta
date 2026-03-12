import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../core/image_service.dart';

/// 증강 아이콘 위젯
/// Silver: 회색 테두리 / Gold: 황금 테두리 / Prismatic: 보라-파랑 그라디언트 테두리
class AugmentIcon extends StatelessWidget {
  final String? imageUrl;
  final String tier;
  final double size;
  final String? name;

  const AugmentIcon({
    super.key,
    required this.tier,
    this.imageUrl,
    this.size = 44,
    this.name,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        children: [
          // 티어별 프레임
          CustomPaint(
            size: Size(size, size),
            painter: _AugmentFramePainter(tier: tier),
          ),
          // 이미지 (패딩으로 프레임 안쪽에 배치)
          Padding(
            padding: EdgeInsets.all(size * 0.1),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: ImageService.augmentImage(
                imageUrl,
                size: size * 0.8,
                fallbackName: name,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AugmentFramePainter extends CustomPainter {
  final String tier;

  const _AugmentFramePainter({required this.tier});

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Rect.fromLTWH(1, 1, size.width - 2, size.height - 2);
    final rrect = RRect.fromRectAndRadius(rect, const Radius.circular(6));

    if (tier == 'Prismatic') {
      _drawPrismaticFrame(canvas, rrect, size);
    } else {
      final color = tier == 'Gold' ? AppColors.gold : const Color(0xFF808080);
      final paint = Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5;
      canvas.drawRRect(rrect, paint);
    }
  }

  void _drawPrismaticFrame(Canvas canvas, RRect rrect, Size size) {
    // 보라 → 파랑 → 보라 그라디언트
    final paint = Paint()
      ..shader = SweepGradient(
        colors: const [
          Color(0xFF9B4FC4),
          Color(0xFF2277BE),
          Color(0xFF2EA94E),
          Color(0xFF9B4FC4),
        ],
        startAngle: 0,
        endAngle: math.pi * 2,
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;
    canvas.drawRRect(rrect, paint);
  }

  @override
  bool shouldRepaint(_AugmentFramePainter old) => old.tier != tier;
}
