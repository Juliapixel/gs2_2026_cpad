class Locality {
  final String uf;
  final String municipality;
  final String? district;

  const Locality({required this.uf, required this.municipality, this.district});

  static const defaultLocality = Locality(
    uf: "SP",
    municipality: "São Paulo",
    district: "Itaquera",
  );

  Locality.fromJson(Map<String, Object?> json)
    : uf = json["uf"] as String? ?? "",
      municipality = json["municipio"] as String? ?? "",
      district = json["distrito"] as String?;

  Map<String, Object?> toJson() => {
    "uf": uf,
    "municipio": municipality,
    "distrito": district,
  };

  Map<String, String> get query => {
    "uf": uf,
    "municipio": municipality,
    if (district != null && district!.isNotEmpty) "distrito": district!,
  };

  String get label => [
    if (district != null && district!.isNotEmpty) district!,
    municipality,
    uf,
  ].join(", ");
}
