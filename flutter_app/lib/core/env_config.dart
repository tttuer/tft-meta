// ignore_for_file: constant_identifier_names

const String env = String.fromEnvironment('ENV', defaultValue: 'development');

class EnvConfig {
  static String get apiBaseUrl {
    switch (env) {
      case 'production':
        return 'https://api.tft-meta.example.com';
      case 'android':
        // Android 에뮬레이터에서 호스트 PC localhost 접근 주소
        return 'http://10.0.2.2:8000';
      default:
        return 'http://localhost:8000';
    }
  }

  static String get compsEndpoint => '/api/v1/comps';
  static String get championsEndpoint => '/api/v1/champions';
  static String get augmentsEndpoint => '/api/v1/augments';
  static String get metaSummaryEndpoint => '/api/v1/meta/summary';
  static String get healthEndpoint => '/health';

  static bool get isProduction => env == 'production';
}
