import 'package:cpad/components/status_badge.dart';
import 'package:flutter/material.dart';

class NoticeBanner extends StatelessWidget {
  final String text;
  final StatusKind kind;
  final IconData icon;

  const NoticeBanner(
    this.text, {
    super.key,
    this.kind = .info,
    this.icon = Icons.info_outline,
  });

  @override
  Widget build(BuildContext context) {
    final (color, background) = kind.colors(context);
    return Container(
      padding: const .all(12),
      decoration: BoxDecoration(color: background, borderRadius: .circular(14)),
      child: Row(
        spacing: 10,
        crossAxisAlignment: .start,
        children: [
          Icon(icon, color: color, size: 20),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall
                  ?.copyWith(color: color, fontWeight: .w500),
            ),
          ),
        ],
      ),
    );
  }
}
