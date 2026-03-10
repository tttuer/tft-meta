import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/comp.dart';
import '../models/champion.dart';
import 'comp_provider.dart';

// 메타 요약
final metaSummaryProvider = FutureProvider<MetaSummary>((ref) async {
  final client = ref.read(apiClientProvider);
  final data = await client.getMetaSummary();
  return MetaSummary.fromJson(data);
});

// 챔피언 목록
final championsProvider = FutureProvider<List<Champion>>((ref) async {
  final client = ref.read(apiClientProvider);
  final data = await client.getChampions();
  return data
      .map((e) => Champion.fromJson(e as Map<String, dynamic>))
      .toList();
});

// 챔피언 맵 (ID → Champion)
final championMapProvider = Provider<AsyncValue<Map<String, Champion>>>((ref) {
  final championsAsync = ref.watch(championsProvider);
  return championsAsync.whenData(
    (champions) => {for (final c in champions) c.id: c},
  );
});

// AI 요약 펼침/접힘 상태
final aiSummaryExpandedProvider = StateProvider<bool>((ref) => false);
