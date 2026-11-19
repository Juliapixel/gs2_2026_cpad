String? validateRequired(String? value) =>
    (value == null || value.isEmpty) ? "Campo obrigatório" : null;

String? validateDescription(String? value, int minLength) {
  final text = value?.trim() ?? "";
  if (text.isEmpty) return "Descreva o que aconteceu";
  if (text.length < minLength) return "Descreva com pelo menos $minLength caracteres (faltam ${minLength - text.length})";
  return null;
}
