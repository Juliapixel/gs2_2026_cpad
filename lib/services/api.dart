import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

const _timeout = Duration(seconds: 8);

/// [cachedAt] is set when the data came from the local cache (offline).
class ApiResponse<T> {
  final T data;
  final DateTime? cachedAt;

  const ApiResponse(this.data, {this.cachedAt});

  ApiResponse<R> map<R>(R Function(T) f) =>
      ApiResponse(f(data), cachedAt: cachedAt);
}

/// HTTP 200 with status "indisponivel".
class NoCoverageException implements Exception {
  final String code;

  const NoCoverageException(this.code);
}

class NoConnectionException implements Exception {
  const NoConnectionException();
}

class ApiException implements Exception {
  final int status;
  final Map<String, Object?> detail;

  const ApiException(this.status, this.detail);

  String get code => detail["codigo"] as String? ?? "erro_$status";

  List<Map<String, Object?>> get fields =>
      (detail["campos"] as List<Object?>? ?? []).cast<Map<String, Object?>>();
}

class FluxoMedApi {
  final Uri base;
  final SharedPreferencesAsync _prefs;

  const FluxoMedApi(this.base, this._prefs);

  Uri _uri(String path, Map<String, String> query) =>
      base.replace(path: path, queryParameters: query.isEmpty ? null : query);

  /// Success stores the response in the cache; a network failure returns the last stored copy.
  Future<ApiResponse<Object?>> get(
    String path, {
    Map<String, String> query = const {},
  }) async {
    final uri = _uri(path, query);
    final key = "cache:$uri";
    http.Response response;
    try {
      response = await http.get(uri).timeout(_timeout);
    } on Exception {
      return _cached(key);
    }
    final body = _decode(response);
    if (body is Map<String, Object?> && body["status"] == "indisponivel") {
      throw NoCoverageException(body["codigo"] as String? ?? "sem_cobertura");
    }
    await _prefs.setString(
      key,
      jsonEncode({"salvo_em": DateTime.now().toIso8601String(), "corpo": body}),
    );
    return ApiResponse(body);
  }

  Future<Object?> post(
    String path,
    Map<String, Object?> body, {
    Map<String, String> query = const {},
  }) async {
    http.Response response;
    try {
      response = await http
          .post(
            _uri(path, query),
            headers: {"content-type": "application/json"},
            body: jsonEncode(body),
          )
          .timeout(_timeout);
    } on Exception {
      throw const NoConnectionException();
    }
    return _decode(response);
  }

  Object? _decode(http.Response response) {
    final Object? body;
    try {
      body = jsonDecode(utf8.decode(response.bodyBytes));
    } on FormatException {
      throw ApiException(response.statusCode, {});
    }
    if (response.statusCode >= 400) {
      final detail = body is Map<String, Object?> ? body["detail"] : null;
      throw ApiException(
        response.statusCode,
        detail is Map<String, Object?> ? detail : {},
      );
    }
    return body;
  }

  Future<ApiResponse<Object?>> _cached(String key) async {
    final stored = await _prefs.getString(key);
    if (stored == null) throw const NoConnectionException();
    final doc = jsonDecode(stored) as Map<String, Object?>;
    return ApiResponse(
      doc["corpo"],
      cachedAt: DateTime.tryParse(doc["salvo_em"] as String? ?? ""),
    );
  }
}

String describeError(Object error) => switch (error) {
  NoConnectionException() => "Não foi possível conectar à API e não há cópia salva para esta localidade.",
  ApiException(:final status, :final code) =>
    "A API respondeu com erro $status ($code).",
  _ => "Algo deu errado: $error",
};
