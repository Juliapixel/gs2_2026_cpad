import 'package:cpad/models/locality.dart';

class AlertSummary {
  final String id;
  final String type;
  final String severity;
  final String unitId;
  final String unitName;
  final int forecastHour;
  final String confidenceLevel;

  AlertSummary.fromJson(Map<String, Object?> json)
    : id = json["id"] as String? ?? "",
      type = json["tipo"] as String? ?? "",
      severity = json["gravidade"] as String? ?? "",
      unitId = json["unidade_id"] as String? ?? "",
      unitName = json["unidade"] as String? ?? "",
      forecastHour = (json["previsao_hora"] as num?)?.toInt() ?? 0,
      confidenceLevel = json["nivel_confianca"] as String? ?? "";
}

class Projection {
  final int valuePct;
  final int minPct;
  final int maxPct;
  final int currentOccupancyPct;
  final int horizonHours;

  Projection.fromJson(Map<String, Object?> json)
    : valuePct = (json["valor_pct"] as num?)?.toInt() ?? 0,
      minPct = (json["faixa_min_pct"] as num?)?.toInt() ?? 0,
      maxPct = (json["faixa_max_pct"] as num?)?.toInt() ?? 0,
      currentOccupancyPct = (json["ocupacao_atual_pct"] as num?)?.toInt() ?? 0,
      horizonHours = (json["horizonte_h"] as num?)?.toInt() ?? 0;
}

/// Only [code] is fixed; [data] varies per reason.
class Reason {
  final String code;
  final Map<String, Object?> data;

  Reason.fromJson(Map<String, Object?> json)
    : code = json["codigo"] as String? ?? "",
      data = json;
}

class Alert extends AlertSummary {
  final Locality territory;
  final Projection projection;
  final int thresholdPct;
  final int durationMin;
  final List<Reason> reasons;
  final double confidence;
  final List<String> limitations;
  final String status;
  final String generatedAt;

  Alert.fromJson(super.json)
    : territory = Locality.fromJson(
        json["territorio"] as Map<String, Object?>? ?? {},
      ),
      projection = Projection.fromJson(
        json["projecao"] as Map<String, Object?>? ?? {},
      ),
      thresholdPct =
          ((json["regra"] as Map<String, Object?>?)?["limiar_pct"] as num?)
              ?.toInt() ??
          0,
      durationMin =
          ((json["regra"] as Map<String, Object?>?)?["duracao_min"] as num?)
              ?.toInt() ??
          0,
      reasons = (json["motivos"] as List<Object?>? ?? [])
          .map((r) => Reason.fromJson(r as Map<String, Object?>))
          .toList(),
      confidence = (json["confianca"] as num?)?.toDouble() ?? 0,
      limitations = (json["limitacoes"] as List<Object?>? ?? []).cast<String>(),
      status = json["status"] as String? ?? "",
      generatedAt = json["gerado_em"] as String? ?? "",
      super.fromJson();
}
