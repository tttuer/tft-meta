import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';
import '../core/constants.dart';
import '../providers/meta_provider.dart';
import '../providers/comp_provider.dart';
import '../widgets/comp_card.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final metaAsync = ref.watch(metaSummaryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'TFT Meta Advisor',
              style: TextStyle(
                fontSize: AppFontSizes.lg,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
          ],
        ),
        actions: [
          metaAsync.when(
            data: (meta) => Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg,
                vertical: AppSpacing.sm,
              ),
              child: Chip(
                label: Text(
                  'Patch ${meta.patchVersion}',
                  style: const TextStyle(
                    fontSize: AppFontSizes.xs,
                    color: AppColors.gold,
                  ),
                ),
                backgroundColor: AppColors.gold.withAlpha(30),
                side: const BorderSide(color: AppColors.gold, width: 1),
                padding: EdgeInsets.zero,
              ),
            ),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(metaSummaryProvider);
          ref.invalidate(allCompsProvider);
        },
        child: ListView(
          padding: const EdgeInsets.only(bottom: AppSpacing.xxl),
          children: [
            // 메타 요약 배너
            _MetaSummaryBanner(),
            const SizedBox(height: AppSpacing.xl),

            // 추천 컴프 TOP 5 헤더
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Row(
                children: [
                  const Text(
                    '추천 컴프 TOP 5',
                    style: TextStyle(
                      fontSize: AppFontSizes.xl,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: () => context.push('/comps'),
                    child: const Text(
                      '전체 보기',
                      style: TextStyle(
                        color: AppColors.accent,
                        fontSize: AppFontSizes.sm,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // TOP 5 컴프 목록
            _TopCompsList(),
          ],
        ),
      ),
    );
  }
}

class _MetaSummaryBanner extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final metaAsync = ref.watch(metaSummaryProvider);
    final isExpanded = ref.watch(aiSummaryExpandedProvider);

    return metaAsync.when(
      data: (meta) => Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md,
        ),
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppColors.primary.withAlpha(153),
                AppColors.surface,
              ],
            ),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.primary, width: 1),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: Row(
                  children: [
                    const Icon(
                      Icons.auto_awesome,
                      color: AppColors.gold,
                      size: 20,
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    const Expanded(
                      child: Text(
                        'AI 메타 요약',
                        style: TextStyle(
                          fontSize: AppFontSizes.lg,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                    // 업데이트 시각
                    Text(
                      '07:00 업데이트',
                      style: const TextStyle(
                        fontSize: AppFontSizes.xs,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),

              // AnimatedSize로 접힘/펼침
              AnimatedSize(
                duration: const Duration(milliseconds: 300),
                curve: Curves.easeInOut,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                    AppSpacing.lg,
                    0,
                    AppSpacing.lg,
                    AppSpacing.md,
                  ),
                  child: Text(
                    isExpanded
                        ? meta.aiSummary
                        : _truncate(meta.aiSummary, 100),
                    style: const TextStyle(
                      fontSize: AppFontSizes.md,
                      color: AppColors.textSecondary,
                      height: 1.5,
                    ),
                  ),
                ),
              ),

              // 더보기 / 접기 버튼
              if (meta.aiSummary.length > 100)
                Padding(
                  padding: const EdgeInsets.fromLTRB(
                    AppSpacing.sm,
                    0,
                    AppSpacing.sm,
                    AppSpacing.sm,
                  ),
                  child: TextButton.icon(
                    onPressed: () => ref
                        .read(aiSummaryExpandedProvider.notifier)
                        .state = !isExpanded,
                    icon: Icon(
                      isExpanded
                          ? Icons.keyboard_arrow_up
                          : Icons.keyboard_arrow_down,
                      size: 18,
                      color: AppColors.accent,
                    ),
                    label: Text(
                      isExpanded ? '접기' : '더보기',
                      style: const TextStyle(
                        color: AppColors.accent,
                        fontSize: AppFontSizes.sm,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
      loading: () => Shimmer.fromColors(
        baseColor: AppColors.surface,
        highlightColor: AppColors.divider,
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.lg,
            vertical: AppSpacing.md,
          ),
          child: Container(
            height: 120,
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(14),
            ),
          ),
        ),
      ),
      error: (error, _) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
        child: Container(
          padding: const EdgeInsets.all(AppSpacing.lg),
          decoration: BoxDecoration(
            color: AppColors.error.withAlpha(30),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.error, width: 1),
          ),
          child: const Text(
            '메타 요약을 불러올 수 없습니다.',
            style: TextStyle(color: AppColors.error),
          ),
        ),
      ),
    );
  }

  String _truncate(String text, int maxLength) {
    if (text.length <= maxLength) return text;
    return '${text.substring(0, maxLength)}...';
  }
}

class _TopCompsList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final topCompsAsync = ref.watch(topCompsProvider);

    return topCompsAsync.when(
      data: (comps) => Column(
        children: comps.map((comp) {
          return CompCard(
            comp: comp,
            onTap: () => context.push('/comps/${comp.id}'),
          );
        }).toList(),
      ),
      loading: () => Column(
        children: List.generate(
          5,
          (i) => Shimmer.fromColors(
            baseColor: AppColors.surface,
            highlightColor: AppColors.divider,
            child: const CompCardSkeleton(),
          ),
        ),
      ),
      error: (error, _) => Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Center(
          child: Column(
            children: [
              const Icon(Icons.error_outline, color: AppColors.error, size: 40),
              const SizedBox(height: AppSpacing.sm),
              Text(
                '컴프 목록을 불러올 수 없습니다.\n$error',
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
              const SizedBox(height: AppSpacing.md),
              ElevatedButton(
                onPressed: () => ref.invalidate(allCompsProvider),
                child: const Text('다시 시도'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
