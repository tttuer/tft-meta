# TFT Flutter Dev — Agent Memory

## Project Architecture (STEP 3 완료)

### State Management
- **Riverpod 2.x** (`flutter_riverpod: ^2.5.0`)
- `apiClientProvider`: ApiClient 싱글톤 Provider
- `FutureProvider` / `FutureProvider.family` for async data
- `StateProvider` / `StateProvider.family` for local state (filter, level selection)

### Key Provider Locations
- `lib/providers/comp_provider.dart`: compListFilterProvider, allCompsProvider, filteredCompsProvider, topCompsProvider, compDetailProvider, compBoardProvider, augmentsProvider, selectedLevelProvider
- `lib/providers/meta_provider.dart`: metaSummaryProvider, championsProvider, championMapProvider, aiSummaryExpandedProvider

### API Client Pattern
- 모든 HTTP 호출은 `lib/core/api_client.dart`의 `ApiClient` 싱글톤 경유
- `EnvConfig.apiBaseUrl` 사용 — URL 하드코딩 금지
- 엔드포인트는 `EnvConfig.*Endpoint` 상수 사용

### Navigation (GoRouter 13.x)
- ShellRoute: `/` (HomeScreen), `/comps` (CompListScreen), `/champions` (ChampionScreen)
- 독립 route: `/comps/:compId` (CompDetailScreen) — ShellRoute 밖

### Board Rendering (CustomPainter)
- `BoardWidget` (StatelessWidget): LayoutBuilder로 반응형 크기 계산
- `_HexGridPainter` (CustomPainter): 빈 슬롯 육각형 점선 테두리 그리기
- `_ChampionCell`: 챔피언 이미지 오버레이 위젯
- 헥사곤 좌표: 짝수 행 0.5 hexW 오프셋 (TFT 표준)
- `BoardWidget.hexOffset()`: static 메서드로 좌표 계산

### Test Pattern
- 테스트에서 네트워크 호출 방지: `ProviderScope(overrides: [championMapProvider.overrideWith(...)])`
- `CompCard`는 내부적으로 `championMapProvider` watch — 테스트 시 반드시 오버라이드 필요

### ChampionIcon Fallback
- `imageUrl` 없을 때 이름 첫 글자 1자만 대문자로 표시 (substring(0, 1))

## File Structure
```
flutter_app/lib/
├── core/         # api_client, env_config, constants, theme
├── models/       # comp, champion, augment
├── providers/    # comp_provider, meta_provider
├── screens/      # home, comp_list, comp_detail, champion
└── widgets/      # comp_card, board_painter, champion_icon, item_icon, tier_badge
```

## Build Commands
- Dev: `flutter run --dart-define=ENV=development`
- Test: `cd flutter_app && flutter test` (24 tests)
- Analyze: `cd flutter_app && flutter analyze`
- Full commands in: `contracts/flutter-build.md`
