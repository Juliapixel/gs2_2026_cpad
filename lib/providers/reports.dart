import 'package:cpad/models/report.dart';
import 'package:cpad/providers/settings.dart';
import 'package:cpad/services/api.dart';
import 'package:riverpod/riverpod.dart';

final reportsProvider = FutureProvider<ApiResponse<List<Report>>>((ref) async {
  final api = await ref.watch(apiProvider.future);
  final response = await api.get("/cidadao/relatos");
  return response.map(
    (body) => (body as List<Object?>).map((r) => Report.fromJson(r as Map<String, Object?>)).toList(),
  );
});

final reportOptionsProvider = FutureProvider<ApiResponse<ReportOptions>>((ref) async {
  final api = await ref.watch(apiProvider.future);
  final locality = await ref.watch(localityProvider.future);
  final response = await api.get("/cidadao/relatos/opcoes", query: locality.query);
  return response.map((body) => ReportOptions.fromJson(body as Map<String, Object?>));
});
