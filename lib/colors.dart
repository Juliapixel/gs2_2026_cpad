import 'package:flutter/material.dart';

@immutable
class FluxoColors extends ThemeExtension<FluxoColors> {
  static const Color _success = Color(0xFF176B4D);
  static const Color _successContainer = Color(0xFFE8F5EE);
  static const Color _warning = Color(0xFF8A4B08);
  static const Color _warningContainer = Color(0xFFFFF3DD);
  final Color success;
  final Color successContainer;
  final Color warning;
  final Color warningContainer;

  const FluxoColors({
    this.success = _success,
    this.successContainer = _successContainer,
    this.warning = _warning,
    this.warningContainer = _warningContainer,
  });

  @override
  ThemeExtension<FluxoColors> copyWith({
    Color? success,
    Color? successContainer,
    Color? warning,
    Color? warningContainer,
  }) {
    return FluxoColors(
      success: success ?? this.success,
      successContainer: successContainer ?? this.successContainer,
      warning: warning ?? this.warning,
      warningContainer: warningContainer ?? this.warningContainer,
    );
  }

  @override
  ThemeExtension<FluxoColors> lerp(
    covariant ThemeExtension<FluxoColors>? other,
    double t,
  ) {
    if (other is! FluxoColors) return this;
    return FluxoColors(
      success: Color.lerp(success, other.success, t) ?? success,
      successContainer: Color.lerp(successContainer, other.successContainer, t) ?? successContainer,
      warning: Color.lerp(warning, other.warning, t) ?? warning,
      warningContainer: Color.lerp(warningContainer, other.warningContainer, t) ?? warningContainer,
    );
  }
}
