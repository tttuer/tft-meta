import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants.dart';
import '../models/comp.dart';
import '../models/champion.dart';
import '../providers/meta_provider.dart';
import 'tier_badge.dart';
import 'champion_icon.dart';

class CompCard extends ConsumerWidget {
  final CompSummary comp;
  final VoidCallback? onTap;

  const CompCard({
    super.key,
    required this.comp,
    this.onTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final championMapAsync = ref.watch(championMapProvider);

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 헤더: 티어 + 이름 + 승률
              Row(
                children: [
                  TierBadge(tier: comp.tier, size: 28, compact: true),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Text(
                      comp.name,
                      style: Theme.of(context).textTheme.titleMedium,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Text(
                    '승률 ${(comp.winRate * 100).toStringAsFixed(1)}%',
                    style: const TextStyle(
                      color: AppColors.gold,
                      fontSize: AppFontSizes.md,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),

              // 챔피언 아이콘 행
              championMapAsync.when(
                data: (championMap) => _buildChampionRow(championMap),
                loading: () => _buildChampionRowSkeleton(),
                error: (_, __) => _buildChampionRowEmpty(),
              ),

              const SizedBox(height: AppSpacing.sm),
              const Divider(height: 1),
              const SizedBox(height: AppSpacing.sm),

              // 하단 스탯 + 화살표
              Row(
                children: [
                  _statItem('평균 순위', comp.avgPlacement.toStringAsFixed(2)),
                  const SizedBox(width: AppSpacing.lg),
                  _statItem(
                      '픽률', '${(comp.playRate * 100).toStringAsFixed(1)}%'),
                  const SizedBox(width: AppSpacing.lg),
                  _statItem(
                      'TOP4', '${(comp.top4Rate * 100).toStringAsFixed(1)}%'),
                  const Spacer(),
                  const Icon(
                    Icons.chevron_right,
                    color: AppColors.textSecondary,
                    size: 20,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChampionRow(Map<String, Champion> championMap) {
    // 코어 챔피언 아이콘 표시 (최대 7개)
    final champions = championMap.values.take(7).toList();
    if (champions.isEmpty) return _buildChampionRowEmpty();

    return SizedBox(
      height: 48,
      child: Row(
        children: champions.map((champion) {
          return Padding(
            padding: const EdgeInsets.only(right: AppSpacing.xs),
            child: ChampionIcon(
              championId: champion.id,
              championName: champion.name,
              cost: champion.cost,
              imageUrl: champion.imageUrl,
              size: 44,
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildChampionRowSkeleton() {
    return SizedBox(
      height: 48,
      child: Row(
        children: List.generate(
          5,
          (i) => Padding(
            padding: const EdgeInsets.only(right: AppSpacing.xs),
            child: Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildChampionRowEmpty() {
    return const SizedBox(height: 48);
  }

  Widget _statItem(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: AppFontSizes.xs,
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: AppFontSizes.sm,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

// Shimmer 스켈레톤 카드
class CompCardSkeleton extends StatelessWidget {
  const CompCardSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _skeletonBox(28, 28, radius: 6),
                const SizedBox(width: AppSpacing.sm),
                _skeletonBox(120, 18, radius: 4),
                const Spacer(),
                _skeletonBox(70, 18, radius: 4),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: List.generate(
                5,
                (i) => Padding(
                  padding: const EdgeInsets.only(right: AppSpacing.xs),
                  child: _skeletonBox(44, 44, radius: 8),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            const Divider(height: 1),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: [
                _skeletonBox(60, 30, radius: 4),
                const SizedBox(width: AppSpacing.lg),
                _skeletonBox(60, 30, radius: 4),
                const SizedBox(width: AppSpacing.lg),
                _skeletonBox(60, 30, radius: 4),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _skeletonBox(double width, double height, {double radius = 4}) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppColors.divider,
        borderRadius: BorderRadius.circular(radius),
      ),
    );
  }
}
