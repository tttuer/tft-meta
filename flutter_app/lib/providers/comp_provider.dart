import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../models/comp.dart';
import '../models/augment.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

// 컴프 목록 - 필터/정렬 상태
class CompListFilter {
  final String? tier;
  final String sortBy; // 'win_rate', 'play_rate', 'avg_placement'
  final String searchQuery;

  const CompListFilter({
    this.tier,
    this.sortBy = 'win_rate',
    this.searchQuery = '',
  });

  CompListFilter copyWith({
    String? tier,
    bool clearTier = false,
    String? sortBy,
    String? searchQuery,
  }) {
    return CompListFilter(
      tier: clearTier ? null : (tier ?? this.tier),
      sortBy: sortBy ?? this.sortBy,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

final compListFilterProvider =
    StateProvider<CompListFilter>((ref) => const CompListFilter());

// 전체 컴프 목록 (limit 100)
final allCompsProvider = FutureProvider<List<CompSummary>>((ref) async {
  final client = ref.read(apiClientProvider);
  final data = await client.getComps(limit: 100);
  return data
      .map((e) => CompSummary.fromJson(e as Map<String, dynamic>))
      .toList();
});

// 필터링/정렬된 컴프 목록
final filteredCompsProvider = Provider<AsyncValue<List<CompSummary>>>((ref) {
  final allCompsAsync = ref.watch(allCompsProvider);
  final filter = ref.watch(compListFilterProvider);

  return allCompsAsync.whenData((comps) {
    var result = comps.where((c) {
      final tierMatch = filter.tier == null || c.tier == filter.tier;
      final searchMatch = filter.searchQuery.isEmpty ||
          c.name.toLowerCase().contains(filter.searchQuery.toLowerCase());
      return tierMatch && searchMatch;
    }).toList();

    switch (filter.sortBy) {
      case 'play_rate':
        result.sort((a, b) => b.playRate.compareTo(a.playRate));
      case 'avg_placement':
        result.sort((a, b) => a.avgPlacement.compareTo(b.avgPlacement));
      default: // 'win_rate'
        result.sort((a, b) => b.winRate.compareTo(a.winRate));
    }
    return result;
  });
});

// 상위 5개 컴프 (홈 화면용)
final topCompsProvider = Provider<AsyncValue<List<CompSummary>>>((ref) {
  final allCompsAsync = ref.watch(allCompsProvider);
  return allCompsAsync.whenData((comps) {
    final sorted = [...comps]..sort((a, b) => b.winRate.compareTo(a.winRate));
    return sorted.take(5).toList();
  });
});

// 컴프 상세
final compDetailProvider =
    FutureProvider.family<CompDetail, String>((ref, compId) async {
  final client = ref.read(apiClientProvider);
  final data = await client.getCompDetail(compId);
  return CompDetail.fromJson(data);
});

// 보드 데이터
final compBoardProvider =
    FutureProvider.family<Board, String>((ref, compId) async {
  final client = ref.read(apiClientProvider);
  final data = await client.getCompBoard(compId);
  return Board.fromJson(data);
});

// 증강 목록
final augmentsProvider =
    FutureProvider.family<List<Augment>, String?>((ref, compId) async {
  final client = ref.read(apiClientProvider);
  final data = await client.getAugments(compId: compId);
  return data
      .map((e) => Augment.fromJson(e as Map<String, dynamic>))
      .toList();
});

// 레벨 선택 (컴프 상세 - 배치 탭)
final selectedLevelProvider = StateProvider.family<int, String>((ref, compId) => 8);
