import 'package:cpad/screens/reports/validation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test("required fields reject empty values", () {
    expect(validateRequired(null), isNotNull);
    expect(validateRequired(""), isNotNull);
    expect(validateRequired("upa-planalto"), isNull);
  });

  test("description enforces minimum length", () {
    expect(validateDescription("", 20), isNotNull);
    expect(validateDescription("curto demais", 20), contains("faltam 8"));
    expect(validateDescription("fila com mais de três horas de espera", 20), isNull);
  });
}
