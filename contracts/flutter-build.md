# Flutter Build Artifacts

## Prerequisites

```bash
cd flutter_app
flutter pub get
```

## Build Commands

### Development
```bash
flutter run --dart-define=ENV=development
```

### Web (Production)
```bash
flutter build web --dart-define=ENV=production
```

### Android APK (Production)
```bash
flutter build apk --dart-define=ENV=production
```

### Android App Bundle (Production, for Play Store)
```bash
flutter build appbundle --dart-define=ENV=production
```

### iOS (Production)
```bash
flutter build ios --dart-define=ENV=production
```

## Artifact Locations

| Platform | Output Path |
|----------|-------------|
| Web      | `flutter_app/build/web/` |
| APK      | `flutter_app/build/app/outputs/flutter-apk/app-release.apk` |
| AAB      | `flutter_app/build/app/outputs/bundle/release/app-release.aab` |
| iOS      | `flutter_app/build/ios/` |

## Environment Variables

The app uses `--dart-define=ENV=<value>` to switch API base URLs:

| ENV value     | API Base URL                          |
|---------------|---------------------------------------|
| `development` | `http://localhost:8000` (default)     |
| `production`  | `https://api.tft-meta.example.com`   |

All URL configuration is in `flutter_app/lib/core/env_config.dart`.
All HTTP calls go through `flutter_app/lib/core/api_client.dart`.

## Test

```bash
cd flutter_app && flutter test
```

Expected: **24 tests passed** (CompCard x6, TierBadge x9, ChampionIcon x9)

## Static Analysis

```bash
cd flutter_app && flutter analyze
```

Expected: **No issues found**

## Architecture Notes

- State management: **Riverpod 2.x** (`flutter_riverpod: ^2.5.0`)
- HTTP client: **Dio 5.x** via `ApiClient` singleton
- Navigation: **GoRouter 13.x** with `ShellRoute` for bottom nav
- Board rendering: **CustomPainter** (`BoardWidget` + `_HexGridPainter`) — 7x4 hexagon grid
- Image caching: `cached_network_image`
- Skeleton loading: `shimmer`
- Local storage: `hive_flutter` (reserved for STEP 4)

## Key Files

| File | Role |
|------|------|
| `lib/core/env_config.dart` | API base URL per environment |
| `lib/core/api_client.dart` | Dio-based HTTP client (all API calls) |
| `lib/core/constants.dart` | Colors, fonts, spacing, board constants |
| `lib/core/theme.dart` | Dark theme definition |
| `lib/models/comp.dart` | CompSummary, CompDetail, Board, MetaSummary |
| `lib/models/champion.dart` | Champion model |
| `lib/models/augment.dart` | Augment model |
| `lib/providers/comp_provider.dart` | Comp list/detail/board providers |
| `lib/providers/meta_provider.dart` | MetaSummary, champions providers |
| `lib/widgets/board_painter.dart` | TFT hex board CustomPainter |
| `lib/screens/home_screen.dart` | Home with meta banner + TOP 5 |
| `lib/screens/comp_list_screen.dart` | Filtered/sorted comp list |
| `lib/screens/comp_detail_screen.dart` | 4-tab detail (board/items/augments/entry) |
| `lib/screens/champion_screen.dart` | Champion guide with cost filter |
