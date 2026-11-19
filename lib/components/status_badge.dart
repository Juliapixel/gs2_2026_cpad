import 'package:cpad/colors.dart';
import 'package:flutter/material.dart';

enum StatusKind {
  ok,
  info,
  warning,
  critical;

  (Color, Color) _getColor(BuildContext context) {
    final theme = Theme.of(context);
    switch (this) {
      case ok:
        return (
          theme.extension<FluxoColors>()!.success,
          theme.extension<FluxoColors>()!.successContainer,
        );
      case info:
        return (theme.primaryColor, theme.colorScheme.primaryContainer);
      case warning:
        return (
          theme.extension<FluxoColors>()!.warning,
          theme.extension<FluxoColors>()!.warningContainer,
        );
      case critical:
        return (theme.colorScheme.error, theme.colorScheme.errorContainer);
    }
  }
}

class StatusBadge extends StatelessWidget {
  final String text;
  final StatusKind kind;

  const StatusBadge(this.text, this.kind, {super.key});

  @override
  Widget build(BuildContext context) {
    final (col, containterCol) = kind._getColor(context);
    final textTheme = Theme.of(context).textTheme;
    return Container(
      height: 32,
      padding: .symmetric(horizontal: 12),
      alignment: .center,
      decoration: BoxDecoration(
        color: containterCol,
        borderRadius: .all(.circular(12.0)),
      ),
      child: Text(
        text,
        style: textTheme.labelMedium?.copyWith(fontWeight: .w600, color: col),
      ),
    );
  }
}
