import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../core/constants.dart';
import '../models/comp.dart';
import '../models/augment.dart';
import '../providers/comp_provider.dart';
import '../providers/meta_provider.dart';
import '../widgets/board_painter.dart';
import '../widgets/champion_icon.dart';
import '../widgets/item_icon.dart';
import '../widgets/tier_badge.dart';

class CompDetailScreen extends ConsumerStatefulWidget {
  final String compId;

  const CompDetailScreen({super.key, required this.compId});

  @override
  ConsumerState<CompDetailScreen> createState() => _CompDetailScreenState();
}

class _CompDetailScreenState extends ConsumerState<CompDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final compAsync = ref.watch(compDetailProvider(widget.compId));

    return compAsync.when(
      data: (comp) => _buildScaffold(comp),
      loading: () => Scaffold(
        appBar: AppBar(title: const Text('로딩 중...')),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (error, _) => Scaffold(
        appBar: AppBar(title: const Text('오류')),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline,
                  color: AppColors.error, size: 48),
              const SizedBox(height: AppSpacing.sm),
              Text('$error',
                  style: const TextStyle(color: AppColors.textSecondary)),
              const SizedBox(height: AppSpacing.md),
              ElevatedButton(
                onPressed: () =>
                    ref.invalidate(compDetailProvider(widget.compId)),
                child: const Text('다시 시도'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildScaffold(CompDetail comp) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            TierBadge(tier: comp.tier, size: 28, compact: true),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Text(
                comp.name,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '배치'),
            Tab(text: '아이템'),
            Tab(text: '증강'),
            Tab(text: '진입조건'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _BoardTab(comp: comp),
          _ItemsTab(comp: comp),
          _AugmentsTab(compId: comp.id),
          _EntryConditionsTab(comp: comp),
        ],
      ),
    );
  }
}

// ── 탭 1: 배치 ──────────────────────────────────────────────────

class _BoardTab extends ConsumerWidget {
  final CompDetail comp;

  const _BoardTab({required this.comp});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final boardAsync = ref.watch(compBoardProvider(comp.id));
    final championMapAsync = ref.watch(championMapProvider);
    final level = ref.watch(selectedLevelProvider(comp.id));

    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 레벨 선택
          Row(
            children: [
              const Text(
                '레벨 선택:',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: AppFontSizes.md,
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              DropdownButton<int>(
                value: level,
                dropdownColor: AppColors.surface,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: AppFontSizes.md,
                ),
                items: [6, 7, 8, 9]
                    .map((l) => DropdownMenuItem(
                          value: l,
                          child: Text('레벨 $l'),
                        ))
                    .toList(),
                onChanged: (v) {
                  if (v == null) return;
                  ref.read(selectedLevelProvider(comp.id).notifier).state = v;
                },
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),

          // 보드 + 레벨 변경 애니메이션
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.divider),
            ),
            padding: const EdgeInsets.all(AppSpacing.sm),
            child: boardAsync.when(
              data: (board) => championMapAsync.when(
                data: (championMap) => BoardWidget(
                  positions: board.boardPositions,
                  championMap: championMap,
                  level: level,
                  coreChampionIds: _getCoreIds(comp),
                ),
                loading: () => _boardSkeleton(),
                error: (_, __) => _boardSkeleton(),
              ),
              loading: () => _boardSkeleton(),
              error: (error, _) => SizedBox(
                height: 200,
                child: Center(
                  child: Text(
                    '배치 데이터를 불러올 수 없습니다.\n$error',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: AppColors.textSecondary),
                  ),
                ),
              ),
            ),
          ),

          const SizedBox(height: AppSpacing.xl),

          // 레전드
          Wrap(
            spacing: AppSpacing.md,
            runSpacing: AppSpacing.sm,
            children: [
              _legendItem(AppColors.gold, '코어 챔피언'),
              ...costColors.entries.map(
                (e) => _legendItem(e.value, '${e.key}코스트'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Set<String> _getCoreIds(CompDetail comp) {
    return comp.coreUnits.keys.toSet();
  }

  Widget _boardSkeleton() {
    return Shimmer.fromColors(
      baseColor: AppColors.surface,
      highlightColor: AppColors.divider,
      child: Container(
        height: 200,
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }

  Widget _legendItem(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color.withAlpha(51),
            borderRadius: BorderRadius.circular(2),
            border: Border.all(color: color, width: 1.5),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: AppFontSizes.xs,
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }
}

// ── 탭 2: 아이템 ─────────────────────────────────────────────────

class _ItemsTab extends ConsumerWidget {
  final CompDetail comp;

  const _ItemsTab({required this.comp});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final championMapAsync = ref.watch(championMapProvider);

    return championMapAsync.when(
      data: (championMap) {
        final coreUnits = comp.coreUnits;
        if (coreUnits.isEmpty) {
          return const Center(
            child: Text(
              '아이템 데이터가 없습니다.',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.all(AppSpacing.lg),
          itemCount: coreUnits.length,
          separatorBuilder: (_, __) => const Divider(),
          itemBuilder: (context, i) {
            final championId = coreUnits.keys.elementAt(i);
            final unitData = coreUnits[championId];
            final champion = championMap[championId];

            final items = unitData is Map
                ? (unitData['items'] as List<dynamic>? ?? [])
                : <dynamic>[];
            final reasoning =
                unitData is Map ? (unitData['reasoning'] as String?) : null;

            return _ChampionItemRow(
              championId: championId,
              champion: champion,
              items: items.map((e) => e.toString()).toList(),
              reasoning: reasoning,
            );
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(
        child: Text('$e',
            style: const TextStyle(color: AppColors.textSecondary)),
      ),
    );
  }
}

class _ChampionItemRow extends StatelessWidget {
  final String championId;
  final dynamic champion;
  final List<String> items;
  final String? reasoning;

  const _ChampionItemRow({
    required this.championId,
    required this.champion,
    required this.items,
    this.reasoning,
  });

  @override
  Widget build(BuildContext context) {
    final cost = champion?.cost as int? ?? 1;
    final name = champion?.name as String? ?? championId;
    final imageUrl = champion?.imageUrl as String?;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ChampionIcon(
            championId: championId,
            championName: name,
            cost: cost,
            imageUrl: imageUrl,
            size: 52,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: AppFontSizes.md,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Row(
                  children: items.take(3).map((itemId) {
                    return Padding(
                      padding: const EdgeInsets.only(right: AppSpacing.xs),
                      child: ItemIcon(itemId: itemId),
                    );
                  }).toList(),
                ),
                if (reasoning != null) ...[
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    reasoning!,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: AppFontSizes.sm,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── 탭 3: 증강 ───────────────────────────────────────────────────

class _AugmentsTab extends ConsumerStatefulWidget {
  final String compId;

  const _AugmentsTab({required this.compId});

  @override
  ConsumerState<_AugmentsTab> createState() => _AugmentsTabState();
}

class _AugmentsTabState extends ConsumerState<_AugmentsTab>
    with SingleTickerProviderStateMixin {
  late TabController _stageTabController;
  static const _stages = ['2-1', '3-2', '4-2'];

  @override
  void initState() {
    super.initState();
    _stageTabController = TabController(length: _stages.length, vsync: this);
  }

  @override
  void dispose() {
    _stageTabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final augmentsAsync = ref.watch(augmentsProvider(widget.compId));

    return Column(
      children: [
        TabBar(
          controller: _stageTabController,
          tabs: _stages.map((s) => Tab(text: 'Stage $s')).toList(),
        ),
        Expanded(
          child: augmentsAsync.when(
            data: (augments) => TabBarView(
              controller: _stageTabController,
              children: _stages
                  .map((stage) => _AugmentStageList(
                        augments: augments,
                        stage: stage,
                      ))
                  .toList(),
            ),
            loading: () =>
                const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(
              child: Text(
                '증강 데이터를 불러올 수 없습니다.\n$e',
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _AugmentStageList extends StatelessWidget {
  final List<Augment> augments;
  final String stage;

  const _AugmentStageList({required this.augments, required this.stage});

  @override
  Widget build(BuildContext context) {
    // 스테이지별 추천: Silver(2-1), Gold(3-2), Prismatic(4-2)
    final tierMap = {'2-1': 'Silver', '3-2': 'Gold', '4-2': 'Prismatic'};
    final preferredTier = tierMap[stage];
    final filtered = preferredTier != null
        ? augments.where((a) => a.tier == preferredTier).take(3).toList()
        : augments.take(3).toList();

    if (filtered.isEmpty) {
      return const Center(
        child: Text(
          '추천 증강이 없습니다.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(AppSpacing.lg),
      itemCount: filtered.length,
      separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.sm),
      itemBuilder: (context, i) => _AugmentCard(augment: filtered[i]),
    );
  }
}

class _AugmentCard extends StatelessWidget {
  final Augment augment;

  const _AugmentCard({required this.augment});

  Color get _tierColor => augmentTierColors[augment.tier] ?? AppColors.textSecondary;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _tierColor.withAlpha(128), width: 1),
      ),
      child: Row(
        children: [
          // 증강 이미지 또는 티어 배지
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: _tierColor.withAlpha(30),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: _tierColor, width: 1.5),
            ),
            child: Center(
              child: Text(
                augment.tier.substring(0, 1),
                style: TextStyle(
                  color: _tierColor,
                  fontWeight: FontWeight.bold,
                  fontSize: AppFontSizes.lg,
                ),
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        augment.name,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: AppFontSizes.md,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.sm,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: _tierColor.withAlpha(30),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        augment.tier,
                        style: TextStyle(
                          color: _tierColor,
                          fontSize: AppFontSizes.xs,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                if (augment.description != null) ...[
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    augment.description!,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: AppFontSizes.sm,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── 탭 4: 진입조건 ───────────────────────────────────────────────

class _EntryConditionsTab extends StatelessWidget {
  final CompDetail comp;

  const _EntryConditionsTab({required this.comp});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 진입 조건 카드 목록
          const Text(
            '진입 조건',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: AppFontSizes.xl,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppSpacing.md),

          if (comp.entryConditions.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
              child: Text(
                '진입 조건 데이터가 없습니다.',
                style: TextStyle(color: AppColors.textSecondary),
              ),
            )
          else
            ...comp.entryConditions.asMap().entries.map((entry) {
              return Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(10),
                    border:
                        Border.all(color: AppColors.divider),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 24,
                        height: 24,
                        decoration: BoxDecoration(
                          color: AppColors.accent.withAlpha(51),
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            '${entry.key + 1}',
                            style: const TextStyle(
                              color: AppColors.accent,
                              fontSize: AppFontSizes.sm,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Text(
                          entry.value,
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: AppFontSizes.md,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),

          // AI 전략 요약
          if (comp.aiSummary != null && comp.aiSummary!.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.xxl),
            const Text(
              'AI 전략 요약',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: AppFontSizes.xl,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            Container(
              padding: const EdgeInsets.all(AppSpacing.lg),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    AppColors.primary.withAlpha(77),
                    AppColors.surface,
                  ],
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.primary, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.auto_awesome,
                          color: AppColors.gold, size: 16),
                      SizedBox(width: AppSpacing.xs),
                      Text(
                        'AI 분석',
                        style: TextStyle(
                          color: AppColors.gold,
                          fontSize: AppFontSizes.sm,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    comp.aiSummary!,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: AppFontSizes.md,
                      height: 1.6,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
