import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';
import '../core/constants.dart';
import '../providers/comp_provider.dart';
import '../widgets/comp_card.dart';

class CompListScreen extends ConsumerStatefulWidget {
  const CompListScreen({super.key});

  @override
  ConsumerState<CompListScreen> createState() => _CompListScreenState();
}

class _CompListScreenState extends ConsumerState<CompListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();

  static const _tiers = ['전체', 'S', 'A', 'B', 'C'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tiers.length, vsync: this);
    _tabController.addListener(_onTabChanged);
    _searchController.addListener(_onSearchChanged);
  }

  void _onTabChanged() {
    if (_tabController.indexIsChanging) return;
    final tier = _tiers[_tabController.index];
    ref.read(compListFilterProvider.notifier).update((state) {
      if (tier == '전체') return state.copyWith(clearTier: true);
      return state.copyWith(tier: tier);
    });
  }

  void _onSearchChanged() {
    ref.read(compListFilterProvider.notifier).update(
          (state) => state.copyWith(searchQuery: _searchController.text),
        );
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('컴프 목록'),
        bottom: TabBar(
          controller: _tabController,
          tabs: _tiers.map((t) => Tab(text: t)).toList(),
          isScrollable: false,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: Column(
        children: [
          // 검색바 + 정렬
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: const InputDecoration(
                      hintText: '컴프 이름 검색...',
                      prefixIcon: Icon(
                        Icons.search,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                _SortDropdown(),
              ],
            ),
          ),

          // 컴프 목록
          Expanded(child: _CompListBody()),
        ],
      ),
    );
  }
}

class _SortDropdown extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filter = ref.watch(compListFilterProvider);

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.divider),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: filter.sortBy,
          dropdownColor: AppColors.surface,
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: AppFontSizes.sm,
          ),
          items: const [
            DropdownMenuItem(value: 'win_rate', child: Text('승률순')),
            DropdownMenuItem(value: 'play_rate', child: Text('픽률순')),
            DropdownMenuItem(
                value: 'avg_placement', child: Text('평균순위순')),
          ],
          onChanged: (value) {
            if (value == null) return;
            ref
                .read(compListFilterProvider.notifier)
                .update((state) => state.copyWith(sortBy: value));
          },
        ),
      ),
    );
  }
}

class _CompListBody extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filteredAsync = ref.watch(filteredCompsProvider);

    return filteredAsync.when(
      data: (comps) {
        if (comps.isEmpty) {
          return const Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.search_off, color: AppColors.textSecondary, size: 48),
                SizedBox(height: AppSpacing.md),
                Text(
                  '조건에 맞는 컴프가 없습니다.',
                  style: TextStyle(color: AppColors.textSecondary),
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.only(bottom: AppSpacing.xxl),
          itemCount: comps.length,
          itemBuilder: (context, index) {
            final comp = comps[index];
            return CompCard(
              comp: comp,
              onTap: () => context.push('/comps/${comp.id}'),
            );
          },
        );
      },
      loading: () => ListView(
        children: List.generate(
          8,
          (i) => Shimmer.fromColors(
            baseColor: AppColors.surface,
            highlightColor: AppColors.divider,
            child: const CompCardSkeleton(),
          ),
        ),
      ),
      error: (error, _) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: AppColors.error, size: 48),
            const SizedBox(height: AppSpacing.sm),
            Text(
              '데이터를 불러올 수 없습니다.\n$error',
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
    );
  }
}
