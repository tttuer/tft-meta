import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../core/constants.dart';
import '../models/champion.dart';
import '../providers/meta_provider.dart';
import '../widgets/champion_icon.dart';
import '../widgets/item_icon.dart';

class ChampionScreen extends ConsumerStatefulWidget {
  const ChampionScreen({super.key});

  @override
  ConsumerState<ChampionScreen> createState() => _ChampionScreenState();
}

class _ChampionScreenState extends ConsumerState<ChampionScreen> {
  final TextEditingController _searchController = TextEditingController();
  int? _selectedCost;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final championsAsync = ref.watch(championsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('챔피언 가이드'),
      ),
      body: Column(
        children: [
          // 검색 + 코스트 필터
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    hintText: '챔피언 이름 검색...',
                    prefixIcon: Icon(
                      Icons.search,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _CostFilterChip(
                        label: '전체',
                        selected: _selectedCost == null,
                        color: AppColors.accent,
                        onSelected: () => setState(() => _selectedCost = null),
                      ),
                      ...costColors.entries.map((e) => _CostFilterChip(
                            label: '${e.key}코스트',
                            selected: _selectedCost == e.key,
                            color: e.value,
                            onSelected: () =>
                                setState(() => _selectedCost = e.key),
                          )),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // 챔피언 목록
          Expanded(
            child: championsAsync.when(
              data: (champions) {
                final filtered = _filterChampions(champions);
                if (filtered.isEmpty) {
                  return const Center(
                    child: Text(
                      '챔피언을 찾을 수 없습니다.',
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.only(
                    left: AppSpacing.lg,
                    right: AppSpacing.lg,
                    bottom: AppSpacing.xxl,
                  ),
                  itemCount: filtered.length,
                  separatorBuilder: (_, __) =>
                      const Divider(height: 1),
                  itemBuilder: (context, i) =>
                      _ChampionRow(champion: filtered[i]),
                );
              },
              loading: () => ListView.builder(
                padding: const EdgeInsets.all(AppSpacing.lg),
                itemCount: 8,
                itemBuilder: (_, __) => Shimmer.fromColors(
                  baseColor: AppColors.surface,
                  highlightColor: AppColors.divider,
                  child: _championSkeleton(),
                ),
              ),
              error: (e, _) => Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline,
                        color: AppColors.error, size: 48),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      '데이터를 불러올 수 없습니다.\n$e',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    ElevatedButton(
                      onPressed: () => ref.invalidate(championsProvider),
                      child: const Text('다시 시도'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<Champion> _filterChampions(List<Champion> all) {
    return all.where((c) {
      final costMatch = _selectedCost == null || c.cost == _selectedCost;
      final searchMatch = _searchController.text.isEmpty ||
          c.name
              .toLowerCase()
              .contains(_searchController.text.toLowerCase());
      return costMatch && searchMatch;
    }).toList()
      ..sort((a, b) {
        final costCmp = a.cost.compareTo(b.cost);
        if (costCmp != 0) return costCmp;
        return a.name.compareTo(b.name);
      });
  }

  Widget _championSkeleton() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                    width: 100, height: 16, color: AppColors.surface),
                const SizedBox(height: 6),
                Container(
                    width: 60, height: 12, color: AppColors.surface),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CostFilterChip extends StatelessWidget {
  final String label;
  final bool selected;
  final Color color;
  final VoidCallback onSelected;

  const _CostFilterChip({
    required this.label,
    required this.selected,
    required this.color,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: AppSpacing.xs),
      child: FilterChip(
        label: Text(
          label,
          style: TextStyle(
            color: selected ? color : AppColors.textSecondary,
            fontSize: AppFontSizes.sm,
          ),
        ),
        selected: selected,
        onSelected: (_) => onSelected(),
        backgroundColor: AppColors.surface,
        selectedColor: color.withAlpha(30),
        side: BorderSide(
          color: selected ? color : AppColors.divider,
          width: selected ? 1.5 : 1,
        ),
        checkmarkColor: color,
        showCheckmark: selected,
      ),
    );
  }
}

class _ChampionRow extends StatelessWidget {
  final Champion champion;

  const _ChampionRow({required this.champion});

  @override
  Widget build(BuildContext context) {
    final bisItems = champion.bestItems.keys.take(3).toList();

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
      child: Row(
        children: [
          ChampionIcon(
            championId: champion.id,
            championName: champion.name,
            cost: champion.cost,
            imageUrl: champion.imageUrl,
            size: 56,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 이름 + 코스트 배지
                Row(
                  children: [
                    Text(
                      champion.name,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.bold,
                        fontSize: AppFontSizes.md,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.xs),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.xs,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: (costColors[champion.cost] ?? AppColors.primary)
                            .withAlpha(40),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                          color: costColors[champion.cost] ??
                              AppColors.primary,
                          width: 1,
                        ),
                      ),
                      child: Text(
                        '${champion.cost}G',
                        style: TextStyle(
                          color: costColors[champion.cost] ??
                              AppColors.textPrimary,
                          fontSize: AppFontSizes.xs,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.xs),

                // 특성 태그
                if (champion.traits.isNotEmpty)
                  Wrap(
                    spacing: 4,
                    children: champion.traits
                        .take(4)
                        .map((trait) => Text(
                              trait,
                              style: const TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: AppFontSizes.xs,
                              ),
                            ))
                        .toList(),
                  ),
              ],
            ),
          ),

          // BIS 아이템 3개
          Row(
            children: bisItems.map((itemId) {
              return Padding(
                padding: const EdgeInsets.only(left: AppSpacing.xs),
                child: ItemIcon(itemId: itemId),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}
