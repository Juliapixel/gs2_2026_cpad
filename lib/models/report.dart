class Report {
  final String id;
  final String unitName;
  final String type;
  final String when;
  final String description;
  final String registeredAt;
  final String status;

  Report.fromJson(Map<String, Object?> json)
    : id = json["id"] as String? ?? "",
      unitName = json["unidade"] as String? ?? "",
      type = json["tipo_ocorrencia"] as String? ?? "",
      when = json["quando"] as String? ?? "",
      description = json["descricao"] as String? ?? "",
      registeredAt = json["registrado_em"] as String? ?? "",
      status = json["status"] as String? ?? "";
}

class UnitOption {
  final String id;
  final String name;

  UnitOption.fromJson(Map<String, Object?> json)
    : id = json["id"] as String? ?? "",
      name = json["nome"] as String? ?? "";
}

class ReportOptions {
  final List<UnitOption> units;
  final List<String> types;
  final List<String> whenOptions;
  final int minDescription;

  ReportOptions.fromJson(Map<String, Object?> json)
    : units = (json["unidades"] as List<Object?>? ?? [])
          .map((u) => UnitOption.fromJson(u as Map<String, Object?>))
          .toList(),
      types = (json["tipos"] as List<Object?>? ?? []).cast<String>(),
      whenOptions = (json["quando"] as List<Object?>? ?? []).cast<String>(),
      minDescription = (json["descricao_min"] as num?)?.toInt() ?? 20;
}
