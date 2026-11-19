import 'package:cpad/colors.dart';
import 'package:cpad/components/fluxo_container.dart';
import 'package:flutter/material.dart';

class StatusCard extends StatelessWidget {
  final String eyebrow;
  final String text;
  final StatusText? status;
  final VoidCallback? onTap;

  const StatusCard(
    this.eyebrow,
    this.text,
    this.status, {
    super.key,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;
    final card = FluxoContainer(
      child: Column(
        spacing: 9,
        crossAxisAlignment: .start,
        children: [
          Text(
            eyebrow,
            style: textTheme.labelLarge?.copyWith(color: theme.hintColor),
            maxLines: 2,
            overflow: .ellipsis,
          ),
          Text(
            text,
            style: textTheme.headlineLarge?.copyWith(fontWeight: .bold),
            maxLines: 1,
            overflow: .ellipsis,
          ),
          ?status,
        ],
      ),
    );
    if (onTap == null) return card;
    return Semantics(
      button: true,
      label: "$eyebrow: $text. Toque para ver detalhes",
      child: InkWell(borderRadius: .circular(14), onTap: onTap, child: card),
    );
  }
}

enum StatusTone { neutral, good, bad }

class StatusText extends StatelessWidget {
  final String text;
  final StatusTone tone;

  const StatusText(this.text, {super.key, this.tone = .neutral});

  Color _color(BuildContext context) => switch (tone) {
    .neutral => Colors.black,
    .good => Theme.of(context).extension<FluxoColors>()!.success,
    .bad => Theme.of(context).colorScheme.error,
  };

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: Theme.of(context).textTheme.labelMedium
          ?.copyWith(color: _color(context)),
      maxLines: 2,
      overflow: .ellipsis,
    );
  }
}
