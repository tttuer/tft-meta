# Frontend Agent Memory

## Project Structure
- `flutter_app/`: Flutter application root
- `lib/core/api_client.dart`: ALL API calls MUST go through this
- `lib/core/env_config.dart`: Environment variables and API base URLs

## Critical Rules
1. **NEVER** make direct HTTP calls - always use `api_client.dart`
2. **NEVER** hardcode API URLs - always use `env_config.dart`
3. **ALWAYS** check `contracts/api-spec.yaml` before implementing API calls
4. **NEVER** modify files outside `flutter_app/` directory

## API Integration Pattern
1. Read `contracts/api-spec.yaml` for endpoint schema
2. Create model class matching response schema
3. Add method to `api_client.dart` using existing patterns
4. Use env variables from `env_config.dart` for base URL

## Build Documentation
- Update `contracts/flutter-build.md` after completing tasks
- Separate Android and iOS build commands
- Include platform-specific requirements

## Platform-Specific Features
### Android Floating Overlay
- Requires `SYSTEM_ALERT_WINDOW` permission
- Use MethodChannel for Flutter-Android communication
- Manage service lifecycle carefully

### iOS Widgets & Live Activities
- WidgetKit framework integration
- ActivityKit for Live Activities
- App Groups for data sharing between app and widgets

## State Management
- TBD: Check existing implementation on first task

## Responsive Design
- Support various screen sizes
- CustomPainter must adapt to different dimensions
