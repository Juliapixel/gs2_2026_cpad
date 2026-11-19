import 'dart:async';
import 'dart:convert';

import 'package:cpad/models/locality.dart';
import 'package:cpad/services/api.dart';
import 'package:flutter/foundation.dart';
import 'package:riverpod/riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _defaultApiHost = kReleaseMode ? "cpad.juliapixel.com" : "localhost:8080";
const _hostKey = "API_HOST";
const _localityKey = "LOCALIDADE";

class Settings {
  final String host;
  final Locality locality;

  const Settings({required this.host, required this.locality});

  Uri get baseUri => kReleaseMode ? Uri.https(host) : Uri.http(host);

  Settings copyWith({String? host, Locality? locality}) =>
      Settings(host: host ?? this.host, locality: locality ?? this.locality);
}

final prefsProvider = Provider<SharedPreferencesAsync>(
  (ref) => SharedPreferencesAsync(),
);

class SettingsNotifier extends AsyncNotifier<Settings> {
  SharedPreferencesAsync get _prefs => ref.read(prefsProvider);

  @override
  FutureOr<Settings> build() async {
    final host = await _prefs.getString(_hostKey);
    final localityJson = await _prefs.getString(_localityKey);
    Locality locality = Locality.defaultLocality;
    if (localityJson != null) {
      locality = Locality.fromJson(
        jsonDecode(localityJson) as Map<String, Object?>,
      );
    }
    return Settings(
      host: (host == null || host.isEmpty) ? _defaultApiHost : host,
      locality: locality,
    );
  }

  Future<void> save({String? host, Locality? locality}) async {
    final current = await future;
    final updated = current.copyWith(host: host, locality: locality);
    await _prefs.setString(_hostKey, updated.host);
    await _prefs.setString(_localityKey, jsonEncode(updated.locality.toJson()));
    state = AsyncData(updated);
  }
}

final settingsProvider = AsyncNotifierProvider<SettingsNotifier, Settings>(
  SettingsNotifier.new,
);

final apiProvider = FutureProvider<FluxoMedApi>((ref) async {
  final settings = await ref.watch(settingsProvider.future);
  return FluxoMedApi(settings.baseUri, ref.watch(prefsProvider));
});

final localityProvider = FutureProvider<Locality>((ref) async {
  return (await ref.watch(settingsProvider.future)).locality;
});
