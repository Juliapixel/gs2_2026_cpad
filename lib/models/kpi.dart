import 'package:cpad/texts.dart';

class Kpi {
  final num value;
  final int? change;
  final String? changeUnit;
  final String? window;
  final String? unit;

  Kpi.fromJson(Map<String, Object?> json)
    : value = json["valor"] as num? ?? 0,
      change = (json["variacao"] as num?)?.toInt(),
      changeUnit = json["unidade_variacao"] as String?,
      window = json["janela"] as String?,
      unit = json["unidade"] as String?;

  String get formattedValue => formatValue(value, unit);

  String? get formattedChange {
    if (change == null) return null;
    final period = window == null ? "" : " ${Texts.translate(Texts.window, window!)}";
    if (change == 0) return "estável$period";
    return "${formatValue(change!.abs(), changeUnit)}$period";
  }

  static String formatValue(num value, String? unit) {
    if (unit == null) return "$value";
    if (unit == "%" || unit == "°C") return "$value$unit";
    return "$value $unit";
  }
}
