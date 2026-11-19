import 'package:cpad/models/alert.dart';
import 'package:cpad/models/dashboard.dart';
import 'package:cpad/providers/settings.dart';
import 'package:cpad/services/api.dart';
import 'package:riverpod/riverpod.dart';

Future<ApiResponse<T>> _fetch<T>(Ref ref, String path, T Function(Map<String, Object?>) parse) async {
  final api = await ref.watch(apiProvider.future);
  final locality = await ref.watch(localityProvider.future);
  final response = await api.get(path, query: locality.query);
  return response.map((body) => parse(body as Map<String, Object?>));
}

final networkProvider = FutureProvider<ApiResponse<Network>>((ref) => _fetch(ref, "/gestor/rede", Network.fromJson));

final capacityProvider = FutureProvider<ApiResponse<Capacity>>(
  (ref) => _fetch(ref, "/gestor/capacidade", Capacity.fromJson),
);

final territoryProvider = FutureProvider<ApiResponse<Territory>>(
  (ref) => _fetch(ref, "/gestor/territorio", Territory.fromJson),
);

final occupancyProvider = FutureProvider<ApiResponse<OccupancyIndicator>>(
  (ref) => _fetch(ref, "/gestor/indicadores/ocupacao", OccupancyIndicator.fromJson),
);

final alertProvider = FutureProvider.family<ApiResponse<Alert>, String>(
  (ref, id) => _fetch(ref, "/gestor/alertas/$id", Alert.fromJson),
);
