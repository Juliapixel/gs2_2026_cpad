import 'package:cpad/models/alert.dart';
import 'package:cpad/models/kpi.dart';

Map<String, Object?> _map(Object? value) => value as Map<String, Object?>? ?? {};

class Network {
  final Kpi occupancy;
  final Kpi averageWait;
  final int unitsInAttention;
  final int totalUnits;
  final int activePlans;
  final Kpi avoidedWait;
  final AlertSummary? highlightedAlert;

  Network.fromJson(Map<String, Object?> json)
    : occupancy = Kpi.fromJson(_map(_map(json["kpis"])["ocupacao_rede"])),
      averageWait = Kpi.fromJson(_map(_map(json["kpis"])["espera_media"])),
      unitsInAttention = (_map(_map(json["kpis"])["em_atencao"])["valor"] as num?)?.toInt() ?? 0,
      totalUnits = (_map(_map(json["kpis"])["em_atencao"])["total"] as num?)?.toInt() ?? 0,
      activePlans = (_map(_map(json["kpis"])["em_atencao"])["plano_ativo"] as num?)?.toInt() ?? 0,
      avoidedWait = Kpi.fromJson(_map(_map(json["kpis"])["espera_evitada"])),
      highlightedAlert = json["alerta_destaque"] == null
          ? null
          : AlertSummary.fromJson(_map(json["alerta_destaque"]));
}

class UnitCapacity {
  final String id;
  final String name;
  final String type;
  final bool open;
  final int occupancyPct;
  final bool aboveThreshold;

  UnitCapacity.fromJson(Map<String, Object?> json)
    : id = json["id"] as String? ?? "",
      name = json["nome"] as String? ?? "",
      type = json["tipo"] as String? ?? "",
      open = json["aberta"] as bool? ?? false,
      occupancyPct = (json["ocupacao_pct"] as num?)?.toInt() ?? 0,
      aboveThreshold = json["acima_do_limite"] as bool? ?? false;
}

class Capacity {
  final int totalUnits;
  final int openUnits;
  final Kpi totalBeds;
  final Kpi freeBeds;
  final Kpi averageWait;
  final Kpi teams;
  final int attentionThresholdPct;
  final List<UnitCapacity> units;

  Capacity.fromJson(Map<String, Object?> json)
    : totalUnits = (json["unidades_total"] as num?)?.toInt() ?? 0,
      openUnits = (json["unidades_abertas"] as num?)?.toInt() ?? 0,
      totalBeds = Kpi.fromJson(_map(_map(json["kpis"])["vagas_totais"])),
      freeBeds = Kpi.fromJson(_map(_map(json["kpis"])["vagas_livres"])),
      averageWait = Kpi.fromJson(_map(_map(json["kpis"])["espera_media"])),
      teams = Kpi.fromJson(_map(_map(json["kpis"])["equipes"])),
      attentionThresholdPct = (json["limiar_atencao_pct"] as num?)?.toInt() ?? 85,
      units = (json["unidades"] as List<Object?>? ?? [])
          .map((u) => UnitCapacity.fromJson(u as Map<String, Object?>))
          .toList();
}

class AreaPriority {
  final String area;
  final String priority;

  AreaPriority.fromJson(Map<String, Object?> json)
    : area = json["area"] as String? ?? "",
      priority = json["prioridade"] as String? ?? "";
}

class Territory {
  final Kpi dayMax;
  final Kpi coverage;
  final int priorityAreas;
  final int totalAreas;
  final Kpi plannedVisits;
  final String areaLevel;
  final List<AreaPriority> priorities;

  Territory.fromJson(Map<String, Object?> json)
    : dayMax = Kpi.fromJson(_map(_map(json["kpis"])["maxima_do_dia"])),
      coverage = Kpi.fromJson(_map(_map(json["kpis"])["cobertura"])),
      priorityAreas = (_map(_map(json["kpis"])["areas_prioritarias"])["valor"] as num?)?.toInt() ?? 0,
      totalAreas = (_map(_map(json["kpis"])["areas_prioritarias"])["total"] as num?)?.toInt() ?? 0,
      plannedVisits = Kpi.fromJson(_map(_map(json["kpis"])["visitas_previstas"])),
      areaLevel = json["nivel_area"] as String? ?? "",
      priorities = (json["prioridades"] as List<Object?>? ?? [])
          .map((p) => AreaPriority.fromJson(p as Map<String, Object?>))
          .toList();
}

class OccupancyPoint {
  final int hour;
  final int occupancyPct;
  final bool projected;

  OccupancyPoint.fromJson(Map<String, Object?> json)
    : hour = (json["hora"] as num?)?.toInt() ?? 0,
      occupancyPct = (json["ocupacao_pct"] as num?)?.toInt() ?? 0,
      projected = json["tipo"] == "projetado";
}

class OccupancyIndicator {
  final int occupancyPct;
  final int occupiedBeds;
  final int totalBeds;
  final int change;
  final String window;
  final int thresholdPct;
  final int durationMin;
  final String highlightedUnit;
  final int highlightedUnitPct;
  final List<OccupancyPoint> points;
  final AlertSummary? highlightedAlert;

  OccupancyIndicator.fromJson(Map<String, Object?> json)
    : occupancyPct = (_map(json["indicador"])["ocupacao_pct"] as num?)?.toInt() ?? 0,
      occupiedBeds = (_map(json["indicador"])["vagas_ocupadas"] as num?)?.toInt() ?? 0,
      totalBeds = (_map(json["indicador"])["vagas_total"] as num?)?.toInt() ?? 0,
      change = (_map(json["indicador"])["variacao"] as num?)?.toInt() ?? 0,
      window = _map(json["indicador"])["janela"] as String? ?? "7d",
      thresholdPct = (_map(_map(json["indicador"])["limiar_atencao"])["limiar_pct"] as num?)?.toInt() ?? 85,
      durationMin = (_map(_map(json["indicador"])["limiar_atencao"])["duracao_min"] as num?)?.toInt() ?? 30,
      highlightedUnit = _map(_map(json["indicador"])["unidade_destaque"])["nome"] as String? ?? "",
      highlightedUnitPct = (_map(_map(json["indicador"])["unidade_destaque"])["ocupacao_pct"] as num?)?.toInt() ?? 0,
      points = (_map(_map(json["indicador"])["grafico"])["pontos"] as List<Object?>? ?? [])
          .map((p) => OccupancyPoint.fromJson(p as Map<String, Object?>))
          .toList(),
      highlightedAlert = json["alerta_destaque"] == null
          ? null
          : AlertSummary.fromJson(_map(json["alerta_destaque"]));
}
