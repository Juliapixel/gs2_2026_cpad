import 'package:cpad/colors.dart';
import 'package:cpad/components/fluxo_container.dart';
import 'package:flutter/material.dart';

class StatusCard extends StatelessWidget {
  final String eyebrow;
  final String text;
  final StatusText status;

  const StatusCard(this.eyebrow, this.text, this.status, {super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;
    return FluxoContainer(
      child: Column(
        spacing: 9,
        crossAxisAlignment: .start,
        children: [
          Text(
            eyebrow,
            style: textTheme.labelLarge?.copyWith(color: theme.hintColor),
            maxLines: 1,
            overflow: .ellipsis,
          ),
          Text(
            text,
            style: textTheme.headlineLarge?.copyWith(fontWeight: .bold),
            maxLines: 1,
            overflow: .ellipsis,
          ),
          status,
        ],
      ),
    );
  }
}

class StatusText extends StatelessWidget {
  final String text;
  Color _getColor(BuildContext context) {
    return Colors.black;
  }

  String get _formattedText => text;

  const StatusText(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Text(
      _formattedText,
      style: Theme.of(context).textTheme.labelMedium
          ?.copyWith(color: _getColor(context)),
      maxLines: 1,
      overflow: .ellipsis,
    );
  }
}

class PositiveStatusText extends StatusText {
  @override
  String get _formattedText => "↑ ${super._formattedText}";

  @override
  Color _getColor(BuildContext context) {
    return Theme.of(context).extension<FluxoColors>()!.success;
  }

  const PositiveStatusText(super.text, {super.key});
}

class NegativeStatusText extends StatusText {
  @override
  String get _formattedText => "↓ ${super._formattedText}";

  @override
  Color _getColor(BuildContext context) {
    return Theme.of(context).colorScheme.error;
  }

  const NegativeStatusText(super.text, {super.key});
}
