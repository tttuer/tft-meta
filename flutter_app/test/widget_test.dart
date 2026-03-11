// TFT Meta Advisor — Widget Tests
// 대상: CompCard, TierBadge, ChampionIcon

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tft_meta_advisor/core/constants.dart';
import 'package:tft_meta_advisor/models/comp.dart';
import 'package:tft_meta_advisor/models/champion.dart';
import 'package:tft_meta_advisor/providers/meta_provider.dart';
import 'package:tft_meta_advisor/widgets/comp_card.dart';
import 'package:tft_meta_advisor/widgets/tier_badge.dart';
import 'package:tft_meta_advisor/widgets/champion_icon.dart';

// 테스트용 더미 챔피언 맵 — API 호출 없이 championMapProvider를 오버라이드
final _emptyChampionMap = <String, Champion>{};

/// 위젯 테스트용 래퍼 — ProviderScope + MaterialApp + 다크 테마 제공
/// championMapProvider를 빈 맵으로 오버라이드하여 네트워크 호출 방지
Widget testApp(Widget child) {
  return ProviderScope(
    overrides: [
      // CompCard 내부에서 championMapProvider를 watch하므로
      // 테스트 환경에서 네트워크 요청이 발생하지 않도록 오버라이드
      championMapProvider.overrideWith(
        (ref) => AsyncValue.data(_emptyChampionMap),
      ),
    ],
    child: MaterialApp(
      theme: ThemeData.dark(),
      home: Scaffold(body: child),
    ),
  );
}

/// 테스트용 CompSummary 픽스처
CompSummary makeComp({
  String tier = 'S',
  double winRate = 0.183,
  double playRate = 0.084,
  double avgPlacement = 3.21,
  double top4Rate = 0.55,
}) {
  return CompSummary(
    id: '00000000-0000-0000-0000-000000000001',
    name: '이렐리아 전사',
    tier: tier,
    winRate: winRate,
    top4Rate: top4Rate,
    avgPlacement: avgPlacement,
    playRate: playRate,
    sampleCount: 10000,
    patchVersion: '14.10',
    updatedAt: DateTime(2026, 3, 10, 7, 0),
  );
}

void main() {
  // ─────────────────────────────────────────────────────────────────────────
  // CompCard 위젯 테스트
  // ─────────────────────────────────────────────────────────────────────────

  group('CompCard', () {
    testWidgets('티어 라벨이 렌더링된다', (tester) async {
      final comp = makeComp(tier: 'S');
      await tester.pumpWidget(testApp(CompCard(comp: comp)));
      await tester.pump();

      // TierBadge compact 모드에서 'S' 텍스트 확인
      expect(find.text('S'), findsOneWidget);
    });

    testWidgets('승률이 소수점 1자리로 표시된다', (tester) async {
      final comp = makeComp(winRate: 0.183);
      await tester.pumpWidget(testApp(CompCard(comp: comp)));
      await tester.pump();

      expect(find.text('승률 18.3%'), findsOneWidget);
    });

    testWidgets('픽률이 올바르게 표시된다', (tester) async {
      final comp = makeComp(playRate: 0.084);
      await tester.pumpWidget(testApp(CompCard(comp: comp)));
      await tester.pump();

      expect(find.text('8.4%'), findsOneWidget);
    });

    testWidgets('평균 순위가 소수점 2자리로 표시된다', (tester) async {
      final comp = makeComp(avgPlacement: 3.21);
      await tester.pumpWidget(testApp(CompCard(comp: comp)));
      await tester.pump();

      expect(find.text('3.21'), findsOneWidget);
    });

    testWidgets('컴프 이름이 표시된다', (tester) async {
      final comp = makeComp();
      await tester.pumpWidget(testApp(CompCard(comp: comp)));
      await tester.pump();

      expect(find.text('이렐리아 전사'), findsOneWidget);
    });

    testWidgets('탭 콜백이 호출된다', (tester) async {
      bool tapped = false;
      final comp = makeComp();
      await tester.pumpWidget(
        testApp(CompCard(comp: comp, onTap: () => tapped = true)),
      );
      await tester.pump();

      await tester.tap(find.byType(InkWell).first);
      expect(tapped, isTrue);
    });
  });

  // ─────────────────────────────────────────────────────────────────────────
  // TierBadge 위젯 테스트
  // ─────────────────────────────────────────────────────────────────────────

  group('TierBadge', () {
    testWidgets('S 티어 텍스트가 표시된다', (tester) async {
      await tester.pumpWidget(testApp(const TierBadge(tier: 'S')));
      await tester.pump();
      expect(find.text('S 티어'), findsOneWidget);
    });

    testWidgets('A 티어 텍스트가 표시된다', (tester) async {
      await tester.pumpWidget(testApp(const TierBadge(tier: 'A')));
      await tester.pump();
      expect(find.text('A 티어'), findsOneWidget);
    });

    testWidgets('B 티어 텍스트가 표시된다', (tester) async {
      await tester.pumpWidget(testApp(const TierBadge(tier: 'B')));
      await tester.pump();
      expect(find.text('B 티어'), findsOneWidget);
    });

    testWidgets('C 티어 텍스트가 표시된다', (tester) async {
      await tester.pumpWidget(testApp(const TierBadge(tier: 'C')));
      await tester.pump();
      expect(find.text('C 티어'), findsOneWidget);
    });

    test('S 티어 색상이 올바르다', () {
      expect(tierColors['S'], equals(const Color(0xFFFF6B35)));
    });

    test('A 티어 색상이 올바르다', () {
      expect(tierColors['A'], equals(const Color(0xFFCDA855)));
    });

    test('B 티어 색상이 올바르다', () {
      expect(tierColors['B'], equals(const Color(0xFF9B9B9B)));
    });

    test('C 티어 색상이 올바르다', () {
      expect(tierColors['C'], equals(const Color(0xFF6B8CAE)));
    });

    testWidgets('compact 모드에서 티어 글자만 표시된다', (tester) async {
      await tester.pumpWidget(testApp(
        const TierBadge(tier: 'S', compact: true),
      ));
      await tester.pump();

      // compact 모드: 'S'만 표시, 'S 티어' 없음
      expect(find.text('S'), findsOneWidget);
      expect(find.text('S 티어'), findsNothing);
    });
  });

  // ─────────────────────────────────────────────────────────────────────────
  // ChampionIcon 위젯 테스트
  // ─────────────────────────────────────────────────────────────────────────

  group('ChampionIcon', () {
    testWidgets('1코스트 챔피언 아이콘이 렌더링된다', (tester) async {
      await tester.pumpWidget(testApp(
        const ChampionIcon(
          championId: 'champion_1',
          championName: 'Test Champion',
          cost: 1,
        ),
      ));
      await tester.pump();
      expect(find.byType(ChampionIcon), findsOneWidget);
    });

    testWidgets('5코스트 챔피언 아이콘이 렌더링된다', (tester) async {
      await tester.pumpWidget(testApp(
        const ChampionIcon(
          championId: 'champion_5',
          championName: 'Legendary',
          cost: 5,
        ),
      ));
      await tester.pump();
      expect(find.byType(ChampionIcon), findsOneWidget);
    });

    testWidgets('imageUrl 없을 때 이니셜 텍스트가 표시된다', (tester) async {
      await tester.pumpWidget(testApp(
        const ChampionIcon(
          championId: 'irelia',
          championName: 'Irelia',
          cost: 4,
        ),
      ));
      await tester.pump();

      // fallback: 이름 첫 글자만 대문자로 표시 ('I')
      expect(find.textContaining('I'), findsOneWidget);
    });

    testWidgets('isCore true 시 위젯이 렌더링된다', (tester) async {
      await tester.pumpWidget(testApp(
        const ChampionIcon(
          championId: 'irelia',
          championName: 'Irelia',
          cost: 4,
          isCore: true,
        ),
      ));
      await tester.pump();
      expect(find.byType(ChampionIcon), findsOneWidget);
    });

    test('1코스트 테두리 색상이 올바르다', () {
      expect(costColors[1], equals(const Color(0xFF808080)));
    });

    test('2코스트 테두리 색상이 올바르다', () {
      expect(costColors[2], equals(const Color(0xFF2EA94E)));
    });

    test('3코스트 테두리 색상이 올바르다', () {
      expect(costColors[3], equals(const Color(0xFF2277BE)));
    });

    test('4코스트 테두리 색상이 올바르다', () {
      expect(costColors[4], equals(const Color(0xFF9B4FC4)));
    });

    test('5코스트 테두리 색상이 올바르다 (골드)', () {
      expect(costColors[5], equals(const Color(0xFFCDA855)));
    });
  });
}
