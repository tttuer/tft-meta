import 'package:dio/dio.dart';
import 'env_config.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;

  ApiClient._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: EnvConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      LogInterceptor(
        request: !EnvConfig.isProduction,
        responseBody: !EnvConfig.isProduction,
        error: true,
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onError: (DioException error, ErrorInterceptorHandler handler) {
          // 에러 로깅 및 공통 처리
          handler.next(error);
        },
      ),
    );
  }

  /// GET /api/v1/comps
  Future<List<dynamic>> getComps({String? tier, int limit = 20}) async {
    final response = await _dio.get(
      EnvConfig.compsEndpoint,
      queryParameters: {
        if (tier != null) 'tier': tier,
        'limit': limit,
      },
    );
    return response.data as List<dynamic>;
  }

  /// GET /api/v1/comps/{comp_id}
  Future<Map<String, dynamic>> getCompDetail(String compId) async {
    final response = await _dio.get('${EnvConfig.compsEndpoint}/$compId');
    return response.data as Map<String, dynamic>;
  }

  /// GET /api/v1/comps/{comp_id}/board
  Future<Map<String, dynamic>> getCompBoard(String compId) async {
    final response = await _dio.get('${EnvConfig.compsEndpoint}/$compId/board');
    return response.data as Map<String, dynamic>;
  }

  /// GET /api/v1/champions
  Future<List<dynamic>> getChampions() async {
    final response = await _dio.get(EnvConfig.championsEndpoint);
    return response.data as List<dynamic>;
  }

  /// GET /api/v1/augments
  Future<List<dynamic>> getAugments({String? compId}) async {
    final response = await _dio.get(
      EnvConfig.augmentsEndpoint,
      queryParameters: {
        if (compId != null) 'comp_id': compId,
      },
    );
    return response.data as List<dynamic>;
  }

  /// GET /api/v1/meta/summary
  Future<Map<String, dynamic>> getMetaSummary() async {
    final response = await _dio.get(EnvConfig.metaSummaryEndpoint);
    return response.data as Map<String, dynamic>;
  }

  /// GET /health
  Future<Map<String, dynamic>> getHealth() async {
    final response = await _dio.get(EnvConfig.healthEndpoint);
    return response.data as Map<String, dynamic>;
  }
}
