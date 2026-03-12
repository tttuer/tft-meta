import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../core/constants.dart';
import '../models/comp.dart';
import '../models/champion.dart';

/// TFT 7×4 헥사곤 그리드 배치 보드 CustomPainter
class BoardWidget extends StatelessWidget {
  final List<BoardPosition> positions;
  final Map<String, Champion> championMap;
  final int level;
  final Set<String>? coreChampionIds;

  const BoardWidget({
    super.key,
    required this.positions,
    required this.championMap,
    this.level = 8,
    this.coreChampionIds,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final availableWidth = constraints.maxWidth;
        // 짝수 행의 0.5칸 오프셋을 고려: 실제 필요 너비 = hexW * 7.5 + 16(패딩)
        // hexW = (availableWidth - 16) / 7.5 로 계산해야 overflow 없음
        final hexW = ((availableWidth - 16) / 7.5).clamp(
          30.0,
          BoardConstants.hexSize,
        );
        final hexH = hexW * 0.866; // sqrt(3)/2 — 정육각형 비율
        final boardHeight = hexH * (BoardConstants.rows + 0.5) + 16;

        // 실제 보드 너비: 7칸 + 짝수행 0.5칸 오프셋 + 양쪽 패딩
        final boardWidth = hexW * 7.5 + 16;

        return SizedBox(
          width: boardWidth,
          height: boardHeight,
          child: Stack(
            children: [
              // 배경 그리드
              CustomPaint(
                size: Size(boardWidth, boardHeight),
                painter: _HexGridPainter(
                  hexW: hexW,
                  hexH: hexH,
                  positions: positions,
                  championMap: championMap,
                ),
              ),
              // 챔피언 이미지 오버레이 (네트워크 이미지는 CustomPainter에서 직접 처리 불가)
              ..._buildChampionOverlays(boardWidth, hexW, hexH),
            ],
          ),
        );
      },
    );
  }

  /// 각 챔피언 슬롯 위치를 계산하고 오버레이 위젯을 생성
  List<Widget> _buildChampionOverlays(
      double boardWidth, double hexW, double hexH) {
    final overlays = <Widget>[];

    for (int row = 0; row < BoardConstants.rows; row++) {
      for (int col = 0; col < BoardConstants.cols; col++) {
        final pos = _findPosition(row, col);
        final offset = _hexOffset(row, col, hexW, hexH);
        final isCore = pos != null &&
            coreChampionIds != null &&
            coreChampionIds!.contains(pos.championId);

        if (pos != null) {
          overlays.add(
            Positioned(
              left: offset.dx,
              top: offset.dy,
              child: _ChampionCell(
                position: pos,
                champion: championMap[pos.championId],
                hexW: hexW,
                hexH: hexH,
                isCore: isCore,
              ),
            ),
          );
        }
      }
    }

    return overlays;
  }

  BoardPosition? _findPosition(int row, int col) {
    try {
      return positions.firstWhere((p) => p.row == row && p.col == col);
    } catch (_) {
      return null;
    }
  }

  /// 짝수 행 오프셋 — TFT 보드의 헥사곤 그리드 좌표계
  static Offset hexOffset(int row, int col, double hexW, double hexH) {
    return _hexOffset(row, col, hexW, hexH);
  }

  static Offset _hexOffset(int row, int col, double hexW, double hexH) {
    final xOffset = (row % 2 == 0) ? hexW * 0.5 : 0.0;
    final x = col * hexW + xOffset + 8;
    final y = row * hexH * 0.75 + 8;
    return Offset(x, y);
  }
}

/// 헥사곤 그리드 배경 페인터
class _HexGridPainter extends CustomPainter {
  final double hexW;
  final double hexH;
  final List<BoardPosition> positions;
  final Map<String, Champion> championMap;

  const _HexGridPainter({
    required this.hexW,
    required this.hexH,
    required this.positions,
    required this.championMap,
  });

  @override
  void paint(Canvas canvas, Size size) {
    for (int row = 0; row < BoardConstants.rows; row++) {
      for (int col = 0; col < BoardConstants.cols; col++) {
        final offset = BoardWidget._hexOffset(row, col, hexW, hexH);
        final hasChampion = positions.any((p) => p.row == row && p.col == col);

        if (!hasChampion) {
          _drawEmptyHex(canvas, offset);
        }
      }
    }
  }

  void _drawEmptyHex(Canvas canvas, Offset topLeft) {
    final cx = topLeft.dx + hexW / 2;
    final cy = topLeft.dy + hexH / 2;
    final r = hexW / 2 * 0.9;

    final path = _hexPath(cx, cy, r);

    final fillPaint = Paint()
      ..color = AppColors.emptySlot
      ..style = PaintingStyle.fill;

    final borderPaint = Paint()
      ..color = AppColors.divider
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    // 점선 효과: 6개 선분을 나눠 그림
    canvas.drawPath(path, fillPaint);
    _drawDashedHexBorder(canvas, cx, cy, r, borderPaint);
  }

  void _drawDashedHexBorder(
      Canvas canvas, double cx, double cy, double r, Paint paint) {
    const dashCount = 3;
    const gapRatio = 0.4;

    for (int i = 0; i < 6; i++) {
      final startAngle = (i * 60 - 30) * math.pi / 180;
      final endAngle = ((i + 1) * 60 - 30) * math.pi / 180;
      final segLen = endAngle - startAngle;
      final dashLen = segLen * (1 - gapRatio) / dashCount;
      final gapLen = segLen * gapRatio / dashCount;

      for (int d = 0; d < dashCount; d++) {
        final s = startAngle + d * (dashLen + gapLen);
        final e = s + dashLen;
        final p = Path();
        p.moveTo(cx + r * math.cos(s), cy + r * math.sin(s));
        p.lineTo(cx + r * math.cos(e), cy + r * math.sin(e));
        canvas.drawPath(p, paint);
      }
    }
  }

  Path _hexPath(double cx, double cy, double r) {
    final path = Path();
    for (int i = 0; i < 6; i++) {
      final angle = (i * 60 - 30) * math.pi / 180;
      final x = cx + r * math.cos(angle);
      final y = cy + r * math.sin(angle);
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    path.close();
    return path;
  }

  @override
  bool shouldRepaint(_HexGridPainter old) {
    return old.hexW != hexW ||
        old.hexH != hexH ||
        old.positions.length != positions.length;
  }
}

/// 개별 챔피언 슬롯 위젯 (이미지 + 테두리 + 아이템 + 별)
class _ChampionCell extends StatelessWidget {
  final BoardPosition position;
  final Champion? champion;
  final double hexW;
  final double hexH;
  final bool isCore;

  const _ChampionCell({
    required this.position,
    required this.champion,
    required this.hexW,
    required this.hexH,
    required this.isCore,
  });

  Color get _borderColor {
    if (isCore) return AppColors.gold;
    final cost = champion?.cost ?? 1;
    return costColors[cost] ?? AppColors.textSecondary;
  }

  @override
  Widget build(BuildContext context) {
    final cellSize = hexW * 0.88;
    final r = cellSize / 2;
    final itemCount = position.items.take(3).length;

    return SizedBox(
      width: hexW,
      height: hexH,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // 챔피언 원형 이미지
          Positioned(
            left: (hexW - cellSize) / 2,
            top: (hexH - cellSize) / 2,
            child: _buildHexChampion(cellSize, r),
          ),

          // 별 등급 (상단)
          if (position.starLevel > 1)
            Positioned(
              top: (hexH - cellSize) / 2 - 12,
              left: 0,
              right: 0,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  position.starLevel,
                  (i) => Icon(
                    Icons.star,
                    size: BoardConstants.starSize,
                    color: position.starLevel == 3
                        ? AppColors.gold
                        : AppColors.textSecondary,
                  ),
                ),
              ),
            ),

          // 아이템 (하단 우측)
          if (itemCount > 0)
            Positioned(
              right: 0,
              bottom: (hexH - cellSize) / 2 - BoardConstants.itemSize * 0.5,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: position.items.take(3).map((itemId) {
                  return Padding(
                    padding: const EdgeInsets.only(left: 1),
                    child: Container(
                      width: BoardConstants.itemSize,
                      height: BoardConstants.itemSize,
                      decoration: BoxDecoration(
                        color: AppColors.primary,
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: AppColors.gold, width: 1),
                      ),
                      child: Center(
                        child: Text(
                          itemId.substring(0, 1).toUpperCase(),
                          style: const TextStyle(
                            color: AppColors.gold,
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildHexChampion(double cellSize, double r) {
    return Container(
      width: cellSize,
      height: cellSize,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: _borderColor,
          width: isCore ? 3.0 : 2.0,
        ),
        color: AppColors.surface,
      ),
      child: ClipOval(
        child: champion?.imageUrl != null
            ? CachedNetworkImage(
                imageUrl: champion!.imageUrl!,
                fit: BoxFit.cover,
                placeholder: (context, url) => _initials(cellSize),
                errorWidget: (context, url, error) => _initials(cellSize),
              )
            : _initials(cellSize),
      ),
    );
  }

  Widget _initials(double cellSize) {
    final name = champion?.name ?? position.championId;
    final cost = champion?.cost ?? 1;
    return Container(
      color: (costColors[cost] ?? AppColors.primary).withAlpha(77),
      child: Center(
        child: Text(
          name.substring(0, math.min(2, name.length)).toUpperCase(),
          style: TextStyle(
            color: costColors[cost] ?? AppColors.textPrimary,
            fontSize: cellSize * 0.3,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
